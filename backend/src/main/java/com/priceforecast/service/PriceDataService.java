package com.priceforecast.service;

import com.priceforecast.entity.PriceData;

import java.time.LocalDate;
import java.util.List;



public interface PriceDataService {

    List<PriceData>queryByGoodsAndDateRange(Long goodsId, LocalDate startDate,LocalDate endDate);

}
