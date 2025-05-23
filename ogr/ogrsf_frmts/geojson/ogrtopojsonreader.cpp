/******************************************************************************
 *
 * Project:  OpenGIS Simple Features Reference Implementation
 * Purpose:  Implementation of OGRTopoJSONReader class
 * Author:   Even Rouault, even dot rouault at spatialys.com
 *
 ******************************************************************************
 * Copyright (c) 2013, Even Rouault <even dot rouault at spatialys.com>
 *
 * SPDX-License-Identifier: MIT
 ****************************************************************************/

#include "ogrgeojsonreader.h"
#include "ogrgeojsonutils.h"
#include "ogrlibjsonutils.h"
#include "ogr_geojson.h"
#include "ogrgeojsongeometry.h"
#include <json.h>  // JSON-C
#include "ogr_api.h"

/************************************************************************/
/*                          OGRTopoJSONReader()                         */
/************************************************************************/

OGRTopoJSONReader::OGRTopoJSONReader() : poGJObject_(nullptr)
{
}

/************************************************************************/
/*                         ~OGRTopoJSONReader()                         */
/************************************************************************/

OGRTopoJSONReader::~OGRTopoJSONReader()
{
    if (nullptr != poGJObject_)
    {
        json_object_put(poGJObject_);
    }

    poGJObject_ = nullptr;
}

/************************************************************************/
/*                           Parse()                                    */
/************************************************************************/

OGRErr OGRTopoJSONReader::Parse(const char *pszText, bool bLooseIdentification)
{
    json_object *jsobj = nullptr;
    if (bLooseIdentification)
    {
        CPLPushErrorHandler(CPLQuietErrorHandler);
    }
    const bool bOK = nullptr != pszText && OGRJSonParse(pszText, &jsobj, true);
    if (bLooseIdentification)
    {
        CPLPopErrorHandler();
        CPLErrorReset();
    }
    if (!bOK)
    {
        return OGRERR_CORRUPT_DATA;
    }

    // JSON tree is shared for while lifetime of the reader object
    // and will be released in the destructor.
    poGJObject_ = jsobj;
    return OGRERR_NONE;
}

typedef struct
{
    double dfScale0;
    double dfScale1;
    double dfTranslate0;
    double dfTranslate1;
    bool bElementExists;
} ScalingParams;

/************************************************************************/
/*                            ParsePoint()                              */
/************************************************************************/

static bool ParsePoint(json_object *poPoint, double *pdfX, double *pdfY)
{
    if (poPoint != nullptr &&
        json_type_array == json_object_get_type(poPoint) &&
        json_object_array_length(poPoint) == 2)
    {
        json_object *poX = json_object_array_get_idx(poPoint, 0);
        json_object *poY = json_object_array_get_idx(poPoint, 1);
        if (poX != nullptr &&
            (json_type_int == json_object_get_type(poX) ||
             json_type_double == json_object_get_type(poX)) &&
            poY != nullptr &&
            (json_type_int == json_object_get_type(poY) ||
             json_type_double == json_object_get_type(poY)))
        {
            *pdfX = json_object_get_double(poX);
            *pdfY = json_object_get_double(poY);
            return true;
        }
    }
    return false;
}

/************************************************************************/
/*                             ParseArc()                               */
/************************************************************************/

static void ParseArc(OGRLineString *poLS, json_object *poArcsDB, int nArcID,
                     bool bReverse, ScalingParams *psParams)
{
    json_object *poArcDB = json_object_array_get_idx(poArcsDB, nArcID);
    if (poArcDB == nullptr || json_type_array != json_object_get_type(poArcDB))
        return;
    auto nPoints = json_object_array_length(poArcDB);
    double dfAccX = 0.0;
    double dfAccY = 0.0;
    int nBaseIndice = poLS->getNumPoints();
    for (auto i = decltype(nPoints){0}; i < nPoints; i++)
    {
        json_object *poPoint = json_object_array_get_idx(poArcDB, i);
        double dfX = 0.0;
        double dfY = 0.0;
        if (ParsePoint(poPoint, &dfX, &dfY))
        {
            if (psParams->bElementExists)
            {
                dfAccX += dfX;
                dfAccY += dfY;
                dfX = dfAccX * psParams->dfScale0 + psParams->dfTranslate0;
                dfY = dfAccY * psParams->dfScale1 + psParams->dfTranslate1;
            }
            else
            {
                dfX = dfX * psParams->dfScale0 + psParams->dfTranslate0;
                dfY = dfY * psParams->dfScale1 + psParams->dfTranslate1;
            }
            if (i == 0)
            {
                if (!bReverse && poLS->getNumPoints() > 0)
                {
                    poLS->setNumPoints(nBaseIndice + static_cast<int>(nPoints) -
                                       1);
                    nBaseIndice--;
                    continue;
                }
                else if (bReverse && poLS->getNumPoints() > 0)
                {
                    poLS->setNumPoints(nBaseIndice + static_cast<int>(nPoints) -
                                       1);
                    nPoints--;
                    if (nPoints == 0)
                        break;
                }
                else
                    poLS->setNumPoints(nBaseIndice + static_cast<int>(nPoints));
            }

            if (!bReverse)
                poLS->setPoint(nBaseIndice + static_cast<int>(i), dfX, dfY);
            else
                poLS->setPoint(nBaseIndice + static_cast<int>(nPoints) - 1 -
                                   static_cast<int>(i),
                               dfX, dfY);
        }
    }
}

/************************************************************************/
/*                        ParseLineString()                             */
/************************************************************************/

static void ParseLineString(OGRLineString *poLS, json_object *poRing,
                            json_object *poArcsDB, ScalingParams *psParams)
{
    const auto nArcsDB = json_object_array_length(poArcsDB);

    const auto nArcsRing = json_object_array_length(poRing);
    for (auto j = decltype(nArcsRing){0}; j < nArcsRing; j++)
    {
        json_object *poArcId = json_object_array_get_idx(poRing, j);
        if (poArcId != nullptr &&
            json_type_int == json_object_get_type(poArcId))
        {
            int nArcId = json_object_get_int(poArcId);
            bool bReverse = false;
            if (nArcId < 0)
            {
                nArcId = -(nArcId + 1);
                bReverse = true;
            }
            if (nArcId < static_cast<int>(nArcsDB))
            {
                ParseArc(poLS, poArcsDB, nArcId, bReverse, psParams);
            }
        }
    }
}

/************************************************************************/
/*                          ParsePolygon()                              */
/************************************************************************/

static void ParsePolygon(OGRPolygon *poPoly, json_object *poArcsObj,
                         json_object *poArcsDB, ScalingParams *psParams)
{
    const auto nRings = json_object_array_length(poArcsObj);
    for (auto i = decltype(nRings){0}; i < nRings; i++)
    {
        OGRLinearRing *poLR = new OGRLinearRing();

        json_object *poRing = json_object_array_get_idx(poArcsObj, i);
        if (poRing != nullptr &&
            json_type_array == json_object_get_type(poRing))
        {
            ParseLineString(poLR, poRing, poArcsDB, psParams);
        }
        poLR->closeRings();
        if (poLR->getNumPoints() < 4)
        {
            CPLDebug("TopoJSON", "Discarding polygon ring made of %d points",
                     poLR->getNumPoints());
            delete poLR;
        }
        else
        {
            poPoly->addRingDirectly(poLR);
        }
    }
}

/************************************************************************/
/*                       ParseMultiLineString()                         */
/************************************************************************/

static void ParseMultiLineString(OGRMultiLineString *poMLS,
                                 json_object *poArcsObj, json_object *poArcsDB,
                                 ScalingParams *psParams)
{
    const auto nRings = json_object_array_length(poArcsObj);
    for (auto i = decltype(nRings){0}; i < nRings; i++)
    {
        OGRLineString *poLS = new OGRLineString();
        poMLS->addGeometryDirectly(poLS);

        json_object *poRing = json_object_array_get_idx(poArcsObj, i);
        if (poRing != nullptr &&
            json_type_array == json_object_get_type(poRing))
        {
            ParseLineString(poLS, poRing, poArcsDB, psParams);
        }
    }
}

/************************************************************************/
/*                       ParseMultiPolygon()                            */
/************************************************************************/

static void ParseMultiPolygon(OGRMultiPolygon *poMultiPoly,
                              json_object *poArcsObj, json_object *poArcsDB,
                              ScalingParams *psParams)
{
    const auto nPolys = json_object_array_length(poArcsObj);
    for (auto i = decltype(nPolys){0}; i < nPolys; i++)
    {
        OGRPolygon *poPoly = new OGRPolygon();

        json_object *poPolyArcs = json_object_array_get_idx(poArcsObj, i);
        if (poPolyArcs != nullptr &&
            json_type_array == json_object_get_type(poPolyArcs))
        {
            ParsePolygon(poPoly, poPolyArcs, poArcsDB, psParams);
        }

        if (poPoly->IsEmpty())
        {
            delete poPoly;
        }
        else
        {
            poMultiPoly->addGeometryDirectly(poPoly);
        }
    }
}

/************************************************************************/
/*                          ParseObject()                               */
/************************************************************************/

static void ParseObject(const char *pszId, json_object *poObj,
                        OGRGeoJSONLayer *poLayer, json_object *poArcsDB,
                        ScalingParams *psParams)
{
    json_object *poType = OGRGeoJSONFindMemberByName(poObj, "type");
    if (poType == nullptr || json_object_get_type(poType) != json_type_string)
        return;
    const char *pszType = json_object_get_string(poType);

    json_object *poArcsObj = OGRGeoJSONFindMemberByName(poObj, "arcs");
    json_object *poCoordinatesObj =
        OGRGeoJSONFindMemberByName(poObj, "coordinates");
    if (strcmp(pszType, "Point") == 0 || strcmp(pszType, "MultiPoint") == 0)
    {
        if (poCoordinatesObj == nullptr ||
            json_type_array != json_object_get_type(poCoordinatesObj))
            return;
    }
    else
    {
        if (poArcsObj == nullptr ||
            json_type_array != json_object_get_type(poArcsObj))
            return;
    }

    if (pszId == nullptr)
    {
        json_object *poId = OGRGeoJSONFindMemberByName(poObj, "id");
        if (poId != nullptr &&
            (json_type_string == json_object_get_type(poId) ||
             json_type_int == json_object_get_type(poId)))
        {
            pszId = json_object_get_string(poId);
        }
    }

    OGRFeature *poFeature = new OGRFeature(poLayer->GetLayerDefn());
    if (pszId != nullptr)
        poFeature->SetField("id", pszId);

    json_object *poProperties = OGRGeoJSONFindMemberByName(poObj, "properties");
    if (poProperties != nullptr &&
        json_type_object == json_object_get_type(poProperties))
    {
        json_object_iter it;
        it.key = nullptr;
        it.val = nullptr;
        it.entry = nullptr;
        json_object_object_foreachC(poProperties, it)
        {
            const int nField = poFeature->GetFieldIndex(it.key);
            OGRGeoJSONReaderSetField(poLayer, poFeature, nField, it.key, it.val,
                                     false, 0);
        }
    }

    OGRGeometry *poGeom = nullptr;
    if (strcmp(pszType, "Point") == 0)
    {
        double dfX = 0.0;
        double dfY = 0.0;
        if (ParsePoint(poCoordinatesObj, &dfX, &dfY))
        {
            dfX = dfX * psParams->dfScale0 + psParams->dfTranslate0;
            dfY = dfY * psParams->dfScale1 + psParams->dfTranslate1;
            poGeom = new OGRPoint(dfX, dfY);
        }
        else
        {
            poGeom = new OGRPoint();
        }
    }
    else if (strcmp(pszType, "MultiPoint") == 0)
    {
        OGRMultiPoint *poMP = new OGRMultiPoint();
        poGeom = poMP;
        const auto nTuples = json_object_array_length(poCoordinatesObj);
        for (auto i = decltype(nTuples){0}; i < nTuples; i++)
        {
            json_object *poPair =
                json_object_array_get_idx(poCoordinatesObj, i);
            double dfX = 0.0;
            double dfY = 0.0;
            if (ParsePoint(poPair, &dfX, &dfY))
            {
                dfX = dfX * psParams->dfScale0 + psParams->dfTranslate0;
                dfY = dfY * psParams->dfScale1 + psParams->dfTranslate1;
                poMP->addGeometryDirectly(new OGRPoint(dfX, dfY));
            }
        }
    }
    else if (strcmp(pszType, "LineString") == 0)
    {
        OGRLineString *poLS = new OGRLineString();
        poGeom = poLS;
        ParseLineString(poLS, poArcsObj, poArcsDB, psParams);
    }
    else if (strcmp(pszType, "MultiLineString") == 0)
    {
        OGRMultiLineString *poMLS = new OGRMultiLineString();
        poGeom = poMLS;
        ParseMultiLineString(poMLS, poArcsObj, poArcsDB, psParams);
    }
    else if (strcmp(pszType, "Polygon") == 0)
    {
        OGRPolygon *poPoly = new OGRPolygon();
        poGeom = poPoly;
        ParsePolygon(poPoly, poArcsObj, poArcsDB, psParams);
    }
    else if (strcmp(pszType, "MultiPolygon") == 0)
    {
        OGRMultiPolygon *poMultiPoly = new OGRMultiPolygon();
        poGeom = poMultiPoly;
        ParseMultiPolygon(poMultiPoly, poArcsObj, poArcsDB, psParams);
    }

    if (poGeom != nullptr)
        poFeature->SetGeometryDirectly(poGeom);
    poLayer->AddFeature(poFeature);
    delete poFeature;
}

/************************************************************************/
/*                        EstablishLayerDefn()                          */
/************************************************************************/

static void
EstablishLayerDefn(int nPrevFieldIdx, std::vector<int> &anCurFieldIndices,
                   std::map<std::string, int> &oMapFieldNameToIdx,
                   std::vector<std::unique_ptr<OGRFieldDefn>> &apoFieldDefn,
                   gdal::DirectedAcyclicGraph<int, std::string> &dag,
                   json_object *poObj,
                   std::set<int> &aoSetUndeterminedTypeFields)
{
    json_object *poObjProps = OGRGeoJSONFindMemberByName(poObj, "properties");
    if (nullptr != poObjProps &&
        json_object_get_type(poObjProps) == json_type_object)
    {
        json_object_iter it;
        it.key = nullptr;
        it.val = nullptr;
        it.entry = nullptr;

        json_object_object_foreachC(poObjProps, it)
        {
            anCurFieldIndices.clear();
            OGRGeoJSONReaderAddOrUpdateField(
                anCurFieldIndices, oMapFieldNameToIdx, apoFieldDefn, it.key,
                it.val, false, 0, false, false, aoSetUndeterminedTypeFields);
            for (int idx : anCurFieldIndices)
            {
                dag.addNode(idx, apoFieldDefn[idx]->GetNameRef());
                if (nPrevFieldIdx != -1)
                {
                    dag.addEdge(nPrevFieldIdx, idx);
                }
                nPrevFieldIdx = idx;
            }
        }
    }
}

/************************************************************************/
/*                        ParseObjectMain()                             */
/************************************************************************/

static bool
ParseObjectMain(const char *pszId, json_object *poObj,
                const OGRSpatialReference *poSRS, OGRGeoJSONDataSource *poDS,
                OGRGeoJSONLayer **ppoMainLayer, json_object *poArcs,
                ScalingParams *psParams, std::vector<int> &anCurFieldIndices,
                std::map<std::string, int> &oMapFieldNameToIdx,
                std::vector<std::unique_ptr<OGRFieldDefn>> &apoFieldDefn,
                gdal::DirectedAcyclicGraph<int, std::string> &dag,
                std::set<int> &aoSetUndeterminedTypeFields)
{
    bool bNeedSecondPass = false;

    if (poObj != nullptr && json_type_object == json_object_get_type(poObj))
    {
        json_object *poType = OGRGeoJSONFindMemberByName(poObj, "type");
        if (poType != nullptr &&
            json_type_string == json_object_get_type(poType))
        {
            const char *pszType = json_object_get_string(poType);
            if (strcmp(pszType, "GeometryCollection") == 0)
            {
                json_object *poGeometries =
                    OGRGeoJSONFindMemberByName(poObj, "geometries");
                if (poGeometries != nullptr &&
                    json_type_array == json_object_get_type(poGeometries))
                {
                    if (pszId == nullptr)
                    {
                        json_object *poId =
                            OGRGeoJSONFindMemberByName(poObj, "id");
                        if (poId != nullptr &&
                            (json_type_string == json_object_get_type(poId) ||
                             json_type_int == json_object_get_type(poId)))
                        {
                            pszId = json_object_get_string(poId);
                        }
                    }

                    OGRGeoJSONLayer *poLayer =
                        new OGRGeoJSONLayer(pszId ? pszId : "TopoJSON", nullptr,
                                            wkbUnknown, poDS, nullptr);
                    poLayer->SetSupportsZGeometries(false);
                    OGRFeatureDefn *poDefn = poLayer->GetLayerDefn();

                    whileUnsealing(poDefn)->GetGeomFieldDefn(0)->SetSpatialRef(
                        poSRS);

                    const auto nGeometries =
                        json_object_array_length(poGeometries);
                    // First pass to establish schema.

                    std::vector<int> anCurFieldIndicesLocal;
                    std::map<std::string, int> oMapFieldNameToIdxLocal;
                    std::vector<std::unique_ptr<OGRFieldDefn>>
                        apoFieldDefnLocal;
                    gdal::DirectedAcyclicGraph<int, std::string> dagLocal;
                    std::set<int> aoSetUndeterminedTypeFieldsLocal;

                    apoFieldDefnLocal.emplace_back(
                        std::make_unique<OGRFieldDefn>("id", OFTString));
                    oMapFieldNameToIdxLocal["id"] = 0;
                    dagLocal.addNode(0, "id");
                    const int nPrevFieldIdx = 0;

                    for (auto i = decltype(nGeometries){0}; i < nGeometries;
                         i++)
                    {
                        json_object *poGeom =
                            json_object_array_get_idx(poGeometries, i);
                        if (poGeom != nullptr &&
                            json_type_object == json_object_get_type(poGeom))
                        {
                            EstablishLayerDefn(
                                nPrevFieldIdx, anCurFieldIndicesLocal,
                                oMapFieldNameToIdxLocal, apoFieldDefnLocal,
                                dagLocal, poGeom,
                                aoSetUndeterminedTypeFieldsLocal);
                        }
                    }

                    const auto sortedFields = dagLocal.getTopologicalOrdering();
                    CPLAssert(sortedFields.size() == apoFieldDefnLocal.size());
                    {
                        auto oTemporaryUnsealer(poDefn->GetTemporaryUnsealer());
                        for (int idx : sortedFields)
                        {
                            poDefn->AddFieldDefn(apoFieldDefnLocal[idx].get());
                        }
                    }

                    // Second pass to build objects.
                    for (auto i = decltype(nGeometries){0}; i < nGeometries;
                         i++)
                    {
                        json_object *poGeom =
                            json_object_array_get_idx(poGeometries, i);
                        if (poGeom != nullptr &&
                            json_type_object == json_object_get_type(poGeom))
                        {
                            ParseObject(nullptr, poGeom, poLayer, poArcs,
                                        psParams);
                        }
                    }

                    poLayer->DetectGeometryType();
                    poDS->AddLayer(poLayer);
                }
            }
            else if (strcmp(pszType, "Point") == 0 ||
                     strcmp(pszType, "MultiPoint") == 0 ||
                     strcmp(pszType, "LineString") == 0 ||
                     strcmp(pszType, "MultiLineString") == 0 ||
                     strcmp(pszType, "Polygon") == 0 ||
                     strcmp(pszType, "MultiPolygon") == 0)
            {
                if (*ppoMainLayer == nullptr)
                {
                    *ppoMainLayer = new OGRGeoJSONLayer(
                        "TopoJSON", nullptr, wkbUnknown, poDS, nullptr);

                    (*ppoMainLayer)->SetSupportsZGeometries(false);

                    whileUnsealing((*ppoMainLayer)->GetLayerDefn())
                        ->GetGeomFieldDefn(0)
                        ->SetSpatialRef(poSRS);

                    apoFieldDefn.emplace_back(
                        std::make_unique<OGRFieldDefn>("id", OFTString));
                    oMapFieldNameToIdx["id"] = 0;
                    dag.addNode(0, "id");
                }

                const int nPrevFieldIdx = 0;
                EstablishLayerDefn(nPrevFieldIdx, anCurFieldIndices,
                                   oMapFieldNameToIdx, apoFieldDefn, dag, poObj,
                                   aoSetUndeterminedTypeFields);

                bNeedSecondPass = true;
            }
        }
    }
    return bNeedSecondPass;
}

/************************************************************************/
/*                     ParseObjectMainSecondPass()                      */
/************************************************************************/

static void ParseObjectMainSecondPass(const char *pszId, json_object *poObj,
                                      OGRGeoJSONLayer **ppoMainLayer,
                                      json_object *poArcs,
                                      ScalingParams *psParams)
{
    if (poObj != nullptr && json_type_object == json_object_get_type(poObj))
    {
        json_object *poType = OGRGeoJSONFindMemberByName(poObj, "type");
        if (poType != nullptr &&
            json_type_string == json_object_get_type(poType))
        {
            const char *pszType = json_object_get_string(poType);
            if (strcmp(pszType, "Point") == 0 ||
                strcmp(pszType, "MultiPoint") == 0 ||
                strcmp(pszType, "LineString") == 0 ||
                strcmp(pszType, "MultiLineString") == 0 ||
                strcmp(pszType, "Polygon") == 0 ||
                strcmp(pszType, "MultiPolygon") == 0)
            {
                ParseObject(pszId, poObj, *ppoMainLayer, poArcs, psParams);
            }
        }
    }
}

/************************************************************************/
/*                           ReadLayers()                               */
/************************************************************************/

void OGRTopoJSONReader::ReadLayers(OGRGeoJSONDataSource *poDS)
{
    if (nullptr == poGJObject_)
    {
        CPLDebug("TopoJSON",
                 "Missing parsed TopoJSON data. Forgot to call Parse()?");
        return;
    }

    poDS->SetSupportsZGeometries(false);

    ScalingParams sParams;
    sParams.dfScale0 = 1.0;
    sParams.dfScale1 = 1.0;
    sParams.dfTranslate0 = 0.0;
    sParams.dfTranslate1 = 0.0;
    sParams.bElementExists = false;
    json_object *poObjTransform =
        OGRGeoJSONFindMemberByName(poGJObject_, "transform");
    if (nullptr != poObjTransform &&
        json_type_object == json_object_get_type(poObjTransform))
    {
        json_object *poObjScale =
            OGRGeoJSONFindMemberByName(poObjTransform, "scale");
        if (nullptr != poObjScale &&
            json_type_array == json_object_get_type(poObjScale) &&
            json_object_array_length(poObjScale) == 2)
        {
            json_object *poScale0 = json_object_array_get_idx(poObjScale, 0);
            json_object *poScale1 = json_object_array_get_idx(poObjScale, 1);
            if (poScale0 != nullptr &&
                (json_object_get_type(poScale0) == json_type_double ||
                 json_object_get_type(poScale0) == json_type_int) &&
                poScale1 != nullptr &&
                (json_object_get_type(poScale1) == json_type_double ||
                 json_object_get_type(poScale1) == json_type_int))
            {
                sParams.dfScale0 = json_object_get_double(poScale0);
                sParams.dfScale1 = json_object_get_double(poScale1);
                sParams.bElementExists = true;
            }
        }

        json_object *poObjTranslate =
            OGRGeoJSONFindMemberByName(poObjTransform, "translate");
        if (nullptr != poObjTranslate &&
            json_type_array == json_object_get_type(poObjTranslate) &&
            json_object_array_length(poObjTranslate) == 2)
        {
            json_object *poTranslate0 =
                json_object_array_get_idx(poObjTranslate, 0);
            json_object *poTranslate1 =
                json_object_array_get_idx(poObjTranslate, 1);
            if (poTranslate0 != nullptr &&
                (json_object_get_type(poTranslate0) == json_type_double ||
                 json_object_get_type(poTranslate0) == json_type_int) &&
                poTranslate1 != nullptr &&
                (json_object_get_type(poTranslate1) == json_type_double ||
                 json_object_get_type(poTranslate1) == json_type_int))
            {
                sParams.dfTranslate0 = json_object_get_double(poTranslate0);
                sParams.dfTranslate1 = json_object_get_double(poTranslate1);
                sParams.bElementExists = true;
            }
        }
    }

    json_object *poArcs = OGRGeoJSONFindMemberByName(poGJObject_, "arcs");
    if (poArcs == nullptr || json_type_array != json_object_get_type(poArcs))
        return;

    OGRGeoJSONLayer *poMainLayer = nullptr;

    json_object *poObjects = OGRGeoJSONFindMemberByName(poGJObject_, "objects");
    if (poObjects == nullptr)
        return;

    OGRSpatialReference *poSRS = OGRGeoJSONReadSpatialReference(poGJObject_);

    std::vector<int> anCurFieldIndices;
    std::map<std::string, int> oMapFieldNameToIdx;
    std::vector<std::unique_ptr<OGRFieldDefn>> apoFieldDefn;
    gdal::DirectedAcyclicGraph<int, std::string> dag;

    std::set<int> aoSetUndeterminedTypeFields;
    if (json_type_object == json_object_get_type(poObjects))
    {
        json_object_iter it;
        it.key = nullptr;
        it.val = nullptr;
        it.entry = nullptr;
        bool bNeedSecondPass = false;
        json_object_object_foreachC(poObjects, it)
        {
            json_object *poObj = it.val;
            bNeedSecondPass |= ParseObjectMain(
                it.key, poObj, poSRS, poDS, &poMainLayer, poArcs, &sParams,
                anCurFieldIndices, oMapFieldNameToIdx, apoFieldDefn, dag,
                aoSetUndeterminedTypeFields);
        }
        if (bNeedSecondPass)
        {
            OGRFeatureDefn *poDefn = poMainLayer->GetLayerDefn();
            const auto sortedFields = dag.getTopologicalOrdering();
            CPLAssert(sortedFields.size() == apoFieldDefn.size());
            auto oTemporaryUnsealer(poDefn->GetTemporaryUnsealer());
            for (int idx : sortedFields)
            {
                poDefn->AddFieldDefn(apoFieldDefn[idx].get());
            }

            it.key = nullptr;
            it.val = nullptr;
            it.entry = nullptr;
            json_object_object_foreachC(poObjects, it)
            {
                json_object *poObj = it.val;
                ParseObjectMainSecondPass(it.key, poObj, &poMainLayer, poArcs,
                                          &sParams);
            }
        }
    }
    else if (json_type_array == json_object_get_type(poObjects))
    {
        const auto nObjects = json_object_array_length(poObjects);
        bool bNeedSecondPass = false;
        for (auto i = decltype(nObjects){0}; i < nObjects; i++)
        {
            json_object *poObj = json_object_array_get_idx(poObjects, i);
            bNeedSecondPass |= ParseObjectMain(
                nullptr, poObj, poSRS, poDS, &poMainLayer, poArcs, &sParams,
                anCurFieldIndices, oMapFieldNameToIdx, apoFieldDefn, dag,
                aoSetUndeterminedTypeFields);
        }
        if (bNeedSecondPass)
        {
            OGRFeatureDefn *poDefn = poMainLayer->GetLayerDefn();
            const auto sortedFields = dag.getTopologicalOrdering();
            CPLAssert(sortedFields.size() == apoFieldDefn.size());
            auto oTemporaryUnsealer(poDefn->GetTemporaryUnsealer());
            for (int idx : sortedFields)
            {
                poDefn->AddFieldDefn(apoFieldDefn[idx].get());
            }

            for (auto i = decltype(nObjects){0}; i < nObjects; i++)
            {
                json_object *poObj = json_object_array_get_idx(poObjects, i);
                ParseObjectMainSecondPass(nullptr, poObj, &poMainLayer, poArcs,
                                          &sParams);
            }
        }
    }

    if (poMainLayer != nullptr)
    {
        poMainLayer->DetectGeometryType();
        poDS->AddLayer(poMainLayer);
    }

    if (poSRS)
        poSRS->Release();
}
