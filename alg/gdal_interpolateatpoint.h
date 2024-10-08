/******************************************************************************
 * $Id$
 *
 * Project:  GDAL Raster Interpolation
 * Purpose:  Interpolation algorithms with cache
 * Author:   Frank Warmerdam, warmerdam@pobox.com
 *
 ******************************************************************************
 * Copyright (c) 2001, Frank Warmerdam
 * Copyright (c) 2008-2012, Even Rouault <even dot rouault at spatialys.com>
 * Copyright (c) 2024, Javier Jimenez Shaw
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 ****************************************************************************/

#ifndef GDAL_INTERPOLATEATPOINT_H_INCLUDED
#define GDAL_INTERPOLATEATPOINT_H_INCLUDED

/*! @cond Doxygen_Suppress */

#include "gdal.h"

#include "cpl_mem_cache.h"
#include "gdal_priv.h"

#include <memory>

using DoublePointsCache =
    lru11::Cache<uint64_t, std::shared_ptr<std::vector<double>>>;

class GDALDoublePointsCache
{
  public:
    std::unique_ptr<DoublePointsCache> cache{};
};

bool GDALInterpolateAtPoint(GDALRasterBand *pBand,
                            GDALRIOResampleAlg eResampleAlg,
                            std::unique_ptr<DoublePointsCache> &cache,
                            const double dfXIn, const double dfYIn,
                            double *pdfOutputReal, double *pdfOutputImag);

/*! @endcond */

#endif /* ndef GDAL_INTERPOLATEATPOINT_H_INCLUDED */
