package com.priceforecast.service.impl;

import com.priceforecast.entity.Forecast;
import com.priceforecast.mapper.ForecastMapper;
import com.priceforecast.service.ForecastService;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class ForecastServiceImpl implements ForecastService {

    private final ForecastMapper forecastMapper;

    // 构造器注入（遵循阿里巴巴Java开发手册，不用 @Autowired 字段注入）
    public ForecastServiceImpl(ForecastMapper forecastMapper) {
        this.forecastMapper = forecastMapper;
    }

    @Override
    public List<Forecast> getFutureForecast(Long goodsId) {
        return forecastMapper.selectByGoodsAndModel(goodsId, "ARIMA");
    }

    @Override
    public List<Forecast> getForecastFrom(Long goodsId, String modelName, LocalDate startDate) {
        return forecastMapper.selectFuture(goodsId, modelName, startDate);
    }
}
