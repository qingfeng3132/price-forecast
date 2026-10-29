package com.priceforecast.service.impl;

import com.priceforecast.entity.PriceData;
import com.priceforecast.mapper.PriceDataMapper;
import com.priceforecast.service.PriceDataService;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class PriceDataServiceImpl  implements PriceDataService {
    private final PriceDataMapper priceDataMapper;


    public PriceDataServiceImpl(PriceDataMapper priceDataMapper){
        this.priceDataMapper =priceDataMapper;

    }
    @Override
    public List<PriceData>queryByGoodsAndDateRange(Long goodsId,LocalDate startDate, LocalDate endDate){
        return priceDataMapper.selectByGoodsAndDateRange(goodsId, startDate, endDate);
    }


}
