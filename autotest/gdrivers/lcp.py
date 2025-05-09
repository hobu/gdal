#!/usr/bin/env pytest
###############################################################################
#
# Project:  GDAL/OGR Test Suite
# Purpose:  Test read functionality for LCP driver.
# Author:   Even Rouault <even dot rouault @ spatialys.com>
#
###############################################################################
# Copyright (c) 2008-2009, Even Rouault <even dot rouault at spatialys.com>
# Copyright (c) 2013, Kyle Shannon <kyle at pobox dot com>
#
# SPDX-License-Identifier: MIT
###############################################################################

import array
import os
import random
import struct

import gdaltest
import pytest

from osgeo import gdal

pytestmark = pytest.mark.require_driver("LCP")

###############################################################################
#  Test test_FARSITE_UTM12.LCP


def test_lcp_1():

    ds = gdal.Open("data/lcp/test_FARSITE_UTM12.LCP")
    assert ds.RasterCount == 8, "wrong number of bands"

    assert (
        ds.GetProjectionRef().find("NAD83 / UTM zone 12N") != -1
    ), "didn't get expect projection. Got : %s" % (ds.GetProjectionRef())

    metadata = [
        ("LATITUDE", "49"),
        ("LINEAR_UNIT", "Meters"),
        (
            "DESCRIPTION",
            "This is a test LCP file created with FARSITE 4.1.054, using data downloaded from the USGS \r\nNational Map for LANDFIRE (2008-05-06). Data were reprojected to UTM zone 12 on NAD83 \r\nusing gdalwarp (GDAL 1.4.2).\r\n",
        ),
    ]
    md = ds.GetMetadata()
    for item in metadata:
        assert (
            md[item[0]] == item[1]
        ), "wrong metadataitem for dataset. md['%s']='%s', expected '%s'" % (
            item[0],
            md[item[0]],
            item[1],
        )

    check_gt = (285807.932887174887583, 30, 0, 5379230.386217921040952, 0, -30)
    new_gt = ds.GetGeoTransform()
    for i in range(6):
        if new_gt[i] != pytest.approx(check_gt[i], abs=1e-5):
            print("")
            print("old = ", check_gt)
            print("new = ", new_gt)
            pytest.fail("Geotransform differs.")

    dataPerBand = [
        (
            18645,
            [
                ("ELEVATION_UNIT", "0"),
                ("ELEVATION_UNIT_NAME", "Meters"),
                ("ELEVATION_MIN", "1064"),
                ("ELEVATION_MAX", "1492"),
                ("ELEVATION_NUM_CLASSES", "-1"),
                ("ELEVATION_FILE", ""),
            ],
        ),
        (
            16431,
            [
                ("SLOPE_UNIT", "0"),
                ("SLOPE_UNIT_NAME", "Degrees"),
                ("SLOPE_MIN", "0"),
                ("SLOPE_MAX", "34"),
                ("SLOPE_NUM_CLASSES", "36"),
                ("SLOPE_FILE", "slope.asc"),
            ],
        ),
        (
            18851,
            [
                ("ASPECT_UNIT", "2"),
                ("ASPECT_UNIT_NAME", "Azimuth degrees"),
                ("ASPECT_MIN", "0"),
                ("ASPECT_MAX", "357"),
                ("ASPECT_NUM_CLASSES", "-1"),
                ("ASPECT_FILE", "aspect.asc"),
            ],
        ),
        (
            26182,
            [
                ("FUEL_MODEL_OPTION", "0"),
                (
                    "FUEL_MODEL_OPTION_DESC",
                    "no custom models AND no conversion file needed",
                ),
                ("FUEL_MODEL_MIN", "1"),
                ("FUEL_MODEL_MAX", "99"),
                ("FUEL_MODEL_NUM_CLASSES", "6"),
                ("FUEL_MODEL_VALUES", "1,2,5,8,10,99"),
                ("FUEL_MODEL_FILE", "fbfm13.asc"),
            ],
        ),
        (
            30038,
            [
                ("CANOPY_COV_UNIT", "0"),
                ("CANOPY_COV_UNIT_NAME", "Categories (0-4)"),
                ("CANOPY_COV_MIN", "0"),
                ("CANOPY_COV_MAX", "95"),
                ("CANOPY_COV_NUM_CLASSES", "10"),
                ("CANOPY_COV_FILE", "cancov.asc"),
            ],
        ),
        (
            22077,
            [
                ("CANOPY_HT_UNIT", "3"),
                ("CANOPY_HT_UNIT_NAME", "Meters x 10"),
                ("CANOPY_HT_MIN", "0"),
                ("CANOPY_HT_MAX", "375"),
                ("CANOPY_HT_NUM_CLASSES", "5"),
                ("CANOPY_HT_FILE", "canht.asc"),
            ],
        ),
        (
            30388,
            [
                ("CBH_UNIT", "3"),
                ("CBH_UNIT_NAME", "Meters x 10"),
                ("CBH_MIN", "0"),
                ("CBH_MAX", "100"),
                ("CBH_NUM_CLASSES", "33"),
                ("CBH_FILE", "cbh.asc"),
            ],
        ),
        (
            23249,
            [
                ("CBD_UNIT", "3"),
                ("CBD_UNIT_NAME", "kg/m^3 x 100"),
                ("CBD_MIN", "0"),
                ("CBD_MAX", "21"),
                ("CBD_NUM_CLASSES", "20"),
                ("CBD_FILE", "cbd.asc"),
            ],
        ),
    ]

    for i in range(8):
        band = ds.GetRasterBand(i + 1)
        assert (
            band.Checksum() == dataPerBand[i][0]
        ), "wrong checksum for band %d. Got %d, expected %d" % (
            i + 1,
            band.Checksum(),
            dataPerBand[i][0],
        )
        md = band.GetMetadata()
        for item in dataPerBand[i][1]:
            assert (
                md[item[0]] == item[1]
            ), "wrong metadataitem for band %d. md['%s']='%s', expected '%s'" % (
                i + 1,
                item[0],
                md[item[0]],
                item[1],
            )

    ds = None


###############################################################################
# test test_USGS_LFNM_Alb83.lcp


def test_lcp_2():

    ds = gdal.Open("data/lcp/test_USGS_LFNM_Alb83.lcp")
    assert ds.RasterCount == 8, "wrong number of bands"

    metadata = [("LATITUDE", "48"), ("LINEAR_UNIT", "Meters"), ("DESCRIPTION", "")]
    md = ds.GetMetadata()
    for item in metadata:
        assert (
            md[item[0]] == item[1]
        ), "wrong metadataitem for dataset. md['%s']='%s', expected '%s'" % (
            item[0],
            md[item[0]],
            item[1],
        )

    check_gt = (-1328145, 30, 0, 2961735, 0, -30)
    new_gt = ds.GetGeoTransform()
    for i in range(6):
        if new_gt[i] != pytest.approx(check_gt[i], abs=1e-5):
            print("")
            print("old = ", check_gt)
            print("new = ", new_gt)
            pytest.fail("Geotransform differs.")

    dataPerBand = [
        (
            28381,
            [
                ("ELEVATION_UNIT", "0"),
                ("ELEVATION_UNIT_NAME", "Meters"),
                ("ELEVATION_MIN", "1064"),
                ("ELEVATION_MAX", "1492"),
                ("ELEVATION_NUM_CLASSES", "-1"),
                (
                    "ELEVATION_FILE",
                    "d:\\scratch\\dist\\79990093\\Output\\rastert_elevation_1.txt",
                ),
            ],
        ),
        (
            25824,
            [
                ("SLOPE_UNIT", "0"),
                ("SLOPE_UNIT_NAME", "Degrees"),
                ("SLOPE_MIN", "0"),
                ("SLOPE_MAX", "34"),
                ("SLOPE_NUM_CLASSES", "35"),
                (
                    "SLOPE_FILE",
                    "d:\\scratch\\dist\\79990093\\Output\\rastert_slope_1.txt",
                ),
            ],
        ),
        (
            28413,
            [
                ("ASPECT_UNIT", "2"),
                ("ASPECT_UNIT_NAME", "Azimuth degrees"),
                ("ASPECT_MIN", "0"),
                ("ASPECT_MAX", "357"),
                ("ASPECT_NUM_CLASSES", "-1"),
                (
                    "ASPECT_FILE",
                    "d:\\scratch\\dist\\79990093\\Output\\rastert_aspect_1.txt",
                ),
            ],
        ),
        (
            19052,
            [
                ("FUEL_MODEL_OPTION", "0"),
                (
                    "FUEL_MODEL_OPTION_DESC",
                    "no custom models AND no conversion file needed",
                ),
                ("FUEL_MODEL_MIN", "1"),
                ("FUEL_MODEL_MAX", "10"),
                ("FUEL_MODEL_NUM_CLASSES", "5"),
                ("FUEL_MODEL_VALUES", "1,2,5,8,10"),
                (
                    "FUEL_MODEL_FILE",
                    "d:\\scratch\\dist\\79990093\\Output\\rastert_fuel1.txt",
                ),
            ],
        ),
        (
            30164,
            [
                ("CANOPY_COV_UNIT", "1"),
                ("CANOPY_COV_UNIT_NAME", "Percent"),
                ("CANOPY_COV_MIN", "0"),
                ("CANOPY_COV_MAX", "95"),
                ("CANOPY_COV_NUM_CLASSES", "10"),
                (
                    "CANOPY_COV_FILE",
                    "d:\\scratch\\dist\\79990093\\Output\\rastert_canopy1.txt",
                ),
            ],
        ),
        (
            22316,
            [
                ("CANOPY_HT_UNIT", "3"),
                ("CANOPY_HT_UNIT_NAME", "Meters x 10"),
                ("CANOPY_HT_MIN", "0"),
                ("CANOPY_HT_MAX", "375"),
                ("CANOPY_HT_NUM_CLASSES", "5"),
                (
                    "CANOPY_HT_FILE",
                    "d:\\scratch\\dist\\79990093\\Output\\rastert_height_1.txt",
                ),
            ],
        ),
        (
            30575,
            [
                ("CBH_UNIT", "3"),
                ("CBH_UNIT_NAME", "Meters x 10"),
                ("CBH_MIN", "0"),
                ("CBH_MAX", "100"),
                ("CBH_NUM_CLASSES", "33"),
                ("CBH_FILE", "d:\\scratch\\dist\\79990093\\Output\\rastert_base_1.txt"),
            ],
        ),
        (
            23304,
            [
                ("CBD_UNIT", "3"),
                ("CBD_UNIT_NAME", "kg/m^3 x 100"),
                ("CBD_MIN", "0"),
                ("CBD_MAX", "21"),
                ("CBD_NUM_CLASSES", "20"),
                (
                    "CBD_FILE",
                    "d:\\scratch\\dist\\79990093\\Output\\rastert_density_1.txt",
                ),
            ],
        ),
    ]

    for i in range(8):
        band = ds.GetRasterBand(i + 1)
        assert (
            band.Checksum() == dataPerBand[i][0]
        ), "wrong checksum for band %d. Got %d, expected %d" % (
            i + 1,
            band.Checksum(),
            dataPerBand[i][0],
        )
        md = band.GetMetadata()
        for item in dataPerBand[i][1]:
            assert (
                md[item[0]] == item[1]
            ), "wrong metadataitem for band %d. md['%s']='%s', expected '%s'" % (
                i + 1,
                item[0],
                md[item[0]],
                item[1],
            )

    ds = None


###############################################################################
#  Test for empty prj


def test_lcp_3():

    ds = gdal.Open("data/lcp/test_USGS_LFNM_Alb83.lcp")
    assert ds is not None
    wkt = ds.GetProjection()
    assert wkt is not None, "Got None from GetProjection()"


###############################################################################
#  Test that the prj file isn't added to the sibling list if it isn't there.


def test_lcp_4():

    ds = gdal.Open("data/lcp/test_USGS_LFNM_Alb83.lcp")
    assert ds is not None
    fl = ds.GetFileList()
    assert len(fl) == 1, "Invalid file list"


###############################################################################
#  Test for valid prj


def test_lcp_5():

    ds = gdal.Open("data/lcp/test_FARSITE_UTM12.LCP")
    assert ds is not None
    wkt = ds.GetProjection()
    assert not (wkt is None or wkt == ""), "Got invalid wkt from GetProjection()"


###############################################################################
#  Test for valid sibling list


def test_lcp_6():

    ds = gdal.Open("data/lcp/test_FARSITE_UTM12.LCP")
    assert ds is not None
    fl = ds.GetFileList()
    try:
        assert len(fl) == 2
    finally:
        ds = None
        try:
            os.remove("data/lcp/test_FARSITE_UTM12.LCP.aux.xml")
        except OSError:
            pass


###############################################################################
#  Test create copy that copies data over


def test_lcp_7():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    lcp_drv = gdal.GetDriverByName("LCP")
    assert lcp_drv is not None
    # Make sure all available band counts work.
    co = ["LATITUDE=0", "LINEAR_UNIT=METER"]
    for i in [5, 7, 8, 10]:
        src_ds = mem_drv.Create("/vsimem/lcptest", 10, 20, i, gdal.GDT_Int16)
        assert src_ds is not None
        dst_ds = lcp_drv.CreateCopy("tmp/lcp_7.lcp", src_ds, False, co)
        assert dst_ds is not None, i
        dst_ds = None
    src_ds = None
    dst_ds = None

    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_7." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy with invalid bands


@gdaltest.disable_exceptions()
def test_lcp_8():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    lcp_drv = gdal.GetDriverByName("LCP")
    assert lcp_drv is not None
    with gdal.quiet_errors():
        co = ["LATITUDE=0", "LINEAR_UNIT=METER"]
        for i in [0, 1, 2, 3, 4, 6, 9, 11]:
            src_ds = mem_drv.Create("", 10, 10, i, gdal.GDT_Int16)
            assert src_ds is not None
            dst_ds = lcp_drv.CreateCopy("tmp/lcp_8.lcp", src_ds, False, co)
            src_ds = None
            assert dst_ds is None, i
            dst_ds = None
    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_8." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy


def test_lcp_9():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    lcp_drv = gdal.GetDriverByName("LCP")
    assert lcp_drv is not None
    src_ds = mem_drv.Create("", 10, 20, 10, gdal.GDT_Int16)
    assert src_ds is not None
    # Test negative values
    src_ds.GetRasterBand(1).Fill(-10000)
    # More than 100 values
    src_ds.GetRasterBand(2).WriteRaster(
        0, 0, 10, 20, array.array("H", [i for i in range(200)])
    )
    co = ["LATITUDE=0", "LINEAR_UNIT=METER"]
    lcp_ds = lcp_drv.CreateCopy("tmp/lcp_9.lcp", src_ds, False, co)
    assert lcp_ds is not None
    lcp_ds = None
    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_9." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure all unit metadata co work


def test_lcp_10():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    for option in ["METERS", "FEET"]:
        co = ["LATITUDE=0", "LINEAR_UNIT=METER", "ELEVATION_UNIT=%s" % option]
        lcp_ds = drv.CreateCopy("tmp/lcp_10.lcp", src_ds, False, co)
        assert lcp_ds is not None
        units = lcp_ds.GetRasterBand(1).GetMetadataItem("ELEVATION_UNIT_NAME")
        assert units.lower() == option.lower()
        lcp_ds = None
    src_ds = None

    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_10." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure all unit metadata co work


def test_lcp_11():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    for option in ["DEGREES", "PERCENT"]:
        co = ["LATITUDE=0", "LINEAR_UNIT=METER", "SLOPE_UNIT=%s" % option]
        lcp_ds = drv.CreateCopy("tmp/lcp_11.lcp", src_ds, False, co)
        assert lcp_ds is not None
        units = lcp_ds.GetRasterBand(2).GetMetadataItem("SLOPE_UNIT_NAME")
        assert units.lower() == option.lower()
        lcp_ds = None
    src_ds = None

    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_11." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure all unit metadata co work


def test_lcp_12():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    for option in ["GRASS_CATEGORIES", "AZIMUTH_DEGREES", "GRASS_DEGREES"]:
        co = ["LATITUDE=0", "LINEAR_UNIT=METER", "ASPECT_UNIT=%s" % option]
        lcp_ds = drv.CreateCopy("tmp/lcp_12.lcp", src_ds, False, co)
        assert lcp_ds is not None
        units = lcp_ds.GetRasterBand(3).GetMetadataItem("ASPECT_UNIT_NAME")
        assert units.lower() == option.replace("_", " ").lower()
        lcp_ds = None
    src_ds = None
    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_12." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure all unit metadata co work


def test_lcp_13():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    for option in ["PERCENT", "CATEGORIES"]:
        co = ["LATITUDE=0", "LINEAR_UNIT=METER", "CANOPY_COV_UNIT=%s" % option]
        lcp_ds = drv.CreateCopy("tmp/lcp_13.lcp", src_ds, False, co)
        assert lcp_ds is not None
        units = lcp_ds.GetRasterBand(5).GetMetadataItem("CANOPY_COV_UNIT_NAME")
        assert units.lower()[:10] == option.lower()[:10]
        lcp_ds = None
    src_ds = None

    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_13." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure all unit metadata co work


def test_lcp_14():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    for option in ["METERS", "FEET", "METERS_X_10", "FEET_X_10"]:
        co = ["LATITUDE=0", "LINEAR_UNIT=METER", "CANOPY_HT_UNIT=%s" % option]
        lcp_ds = drv.CreateCopy("tmp/lcp_14.lcp", src_ds, False, co)
        assert lcp_ds is not None
        units = lcp_ds.GetRasterBand(6).GetMetadataItem("CANOPY_HT_UNIT_NAME")
        assert units.lower() == option.replace("_", " ").lower()
        lcp_ds = None
    src_ds = None

    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_14." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure all unit metadata co work


def test_lcp_15():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    for option in ["METERS", "FEET", "METERS_X_10", "FEET_X_10"]:
        co = ["LATITUDE=0", "LINEAR_UNIT=METER", "CBH_UNIT=%s" % option]
        lcp_ds = drv.CreateCopy("tmp/lcp_15.lcp", src_ds, False, co)
        assert lcp_ds is not None
        units = lcp_ds.GetRasterBand(7).GetMetadataItem("CBH_UNIT_NAME")
        assert units.lower() == option.replace("_", " ").lower()
        lcp_ds = None
    src_ds = None

    for ext in ["lcp", "prj", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_15." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure all unit metadata co work


def test_lcp_16():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    answers = ["kg/m^3", "lb/ft^3", "kg/m^3 x 100", "lb/ft^3 x 1000", "tons/acre x 100"]
    for i, option in enumerate(
        [
            "KG_PER_CUBIC_METER",
            "POUND_PER_CUBIC_FOOT",
            "KG_PER_CUBIC_METER_X_100",
            "POUND_PER_CUBIC_FOOT_X_1000",
        ]
    ):
        co = ["LATITUDE=0", "LINEAR_UNIT=METER", "CBD_UNIT=%s" % option]
        lcp_ds = drv.CreateCopy("tmp/lcp_16.lcp", src_ds, False, co)
        assert lcp_ds is not None
        units = lcp_ds.GetRasterBand(8).GetMetadataItem("CBD_UNIT_NAME")
        assert units.lower() == answers[i].lower()
        lcp_ds = None
    src_ds = None

    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_16." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure all unit metadata co work
#  It is unclear whether the metadata generated is correct, or the
#  documentation.  Docs say mg/ha * 10 and tn/ac * 10, metadata is not * 10.


def test_lcp_17():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    answers = ["mg/ha", "t/ac"]
    for i, option in enumerate(["MG_PER_HECTARE_X_10", "TONS_PER_ACRE_X_10"]):
        co = ["LATITUDE=0", "LINEAR_UNIT=METER", "DUFF_UNIT=%s" % option]
        lcp_ds = drv.CreateCopy("tmp/lcp_17.lcp", src_ds, False, co)
        assert lcp_ds is not None
        units = lcp_ds.GetRasterBand(9).GetMetadataItem("DUFF_UNIT_NAME")
        assert units.lower() == answers[i].lower()
        lcp_ds = None
    src_ds = None

    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_17." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure creation options work.


def test_lcp_18():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    co = ["LATITUDE=45", "LINEAR_UNIT=METER"]
    lcp_ds = drv.CreateCopy("tmp/lcp_18.lcp", src_ds, False, co)
    assert lcp_ds is not None
    assert lcp_ds.GetMetadataItem("LATITUDE") == "45"

    src_ds = None
    lcp_ds = None
    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_18." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure creation options work.


def test_lcp_19():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    co = ["LATITUDE=0", "LINEAR_UNIT=FOOT"]
    lcp_ds = drv.CreateCopy("tmp/lcp_19.lcp", src_ds, False, co)
    assert lcp_ds is not None
    assert lcp_ds.GetMetadataItem("LINEAR_UNIT") == "Feet"

    src_ds = None
    lcp_ds = None
    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_19." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure DESCRIPTION co works


def test_lcp_20():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    desc = "test description"
    co = ["LATITUDE=0", "LINEAR_UNIT=METER", "DESCRIPTION=%s" % desc]
    lcp_ds = drv.CreateCopy("tmp/lcp_20.lcp", src_ds, False, co)
    assert lcp_ds is not None
    assert lcp_ds.GetMetadataItem("DESCRIPTION") == desc
    src_ds = None
    lcp_ds = None
    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_20." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make data is copied over via checksums


def test_lcp_21():
    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 3, 3, 10, gdal.GDT_Int16)
    assert src_ds is not None

    for i in range(10):
        data = [random.randint(0, 100) for i in range(9)]
        src_ds.GetRasterBand(i + 1).WriteRaster(0, 0, 3, 3, struct.pack("h" * 9, *data))

    co = ["LATITUDE=0", "LINEAR_UNIT=METER"]
    lcp_ds = drv.CreateCopy("tmp/lcp_21.lcp", src_ds, False, co)
    assert lcp_ds is not None
    assert [
        src_ds.GetRasterBand(i + 1).Checksum() for i in range(src_ds.RasterCount)
    ] == [lcp_ds.GetRasterBand(i + 1).Checksum() for i in range(lcp_ds.RasterCount)]

    src_ds = None
    lcp_ds = None
    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_21." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make data is copied over via numpy comparison.


def test_lcp_22():

    gdaltest.importorskip_gdal_array()
    numpy = pytest.importorskip("numpy")

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 3, 3, 10, gdal.GDT_Int16)
    assert src_ds is not None

    for i in range(10):
        data = [random.randint(0, 100) for i in range(9)]
        src_ds.GetRasterBand(i + 1).WriteRaster(0, 0, 3, 3, struct.pack("h" * 9, *data))

    co = ["LATITUDE=0", "LINEAR_UNIT=METER"]
    lcp_ds = drv.CreateCopy("tmp/lcp_22.lcp", src_ds, False, co)
    assert lcp_ds is not None
    for i in range(10):
        src_data = src_ds.GetRasterBand(i + 1).ReadAsArray()
        dst_data = lcp_ds.GetRasterBand(i + 1).ReadAsArray()
        assert numpy.array_equal(src_data, dst_data), i
    src_ds = None
    lcp_ds = None
    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_22." + ext)
        except OSError:
            pass


###############################################################################
#  Test create copy and make sure invalid creation options are caught.


@gdaltest.disable_exceptions()
def test_lcp_23():

    mem_drv = gdal.GetDriverByName("MEM")
    assert mem_drv is not None
    drv = gdal.GetDriverByName("LCP")
    assert drv is not None
    src_ds = mem_drv.Create("/vsimem/", 10, 10, 10, gdal.GDT_Int16)
    assert src_ds is not None

    bad = "NOT_A_REAL_OPTION"
    with gdal.quiet_errors():
        for option in [
            "ELEVATION_UNIT",
            "SLOPE_UNIT",
            "ASPECT_UNIT",
            "FUEL_MODEL_OPTION",
            "CANOPY_COV_UNIT",
            "CANOPY_HT_UNIT",
            "CBH_UNIT",
            "CBD_UNIT",
            "DUFF_UNIT",
        ]:
            co = [
                "%s=%s" % (option, bad),
            ]
            lcp_ds = drv.CreateCopy("tmp/lcp_23.lcp", src_ds, False, co)
            assert lcp_ds is None

    src_ds = None
    lcp_ds = None
    for ext in ["lcp", "lcp.aux.xml"]:
        try:
            os.remove("tmp/lcp_23." + ext)
        except OSError:
            pass
