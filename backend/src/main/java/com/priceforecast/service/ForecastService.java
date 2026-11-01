package com.priceforecast.service;

import com.priceforecast.entity.Forecast;

import java.time.LocalDate;
import java.util.List;

public interface ForecastService {

    /**
     * 查询某商品 ARIMA 模型的未来 7 天预测
     */
    List<Forecast> getFutureForecast(Long goodsId);

    /**
     * 查询某商品某模型、从指定日期起的预测
     */
    List<Forecast> getForecastFrom(Long goodsId, String modelName, LocalDate startDate);
}
