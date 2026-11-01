package com.priceforecast.controller;

import com.priceforecast.entity.Forecast;
import com.priceforecast.service.ForecastService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/forecast")
public class ForecastController {

    private final ForecastService forecastService;

    public ForecastController(ForecastService forecastService) {
        this.forecastService = forecastService;
    }

    /**
     * 查询某商品的未来 7 天预测（ARIMA 模型）
     * GET /api/forecast?goodsId=4
     */
    @GetMapping
    public List<Forecast> getForecast(@RequestParam Long goodsId) {
        return forecastService.getFutureForecast(goodsId);
    }
}
