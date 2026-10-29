package com.priceforecast.controller;

import com.priceforecast.service.PriceDataService;
import com.priceforecast.entity.PriceData;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.time.LocalDate;

@RestController
@RequestMapping("/api/price")
public class PriceDataController {
    private final PriceDataService priceDataService;
    public PriceDataController(PriceDataService priceDataService){
        this.priceDataService =  priceDataService;
    }
    @GetMapping
    public  List<PriceData>query(
            @RequestParam Long goodsId,
            @RequestParam @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate startDate,
            @RequestParam @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate endDate
    ){
        return priceDataService.queryByGoodsAndDateRange(goodsId,startDate,endDate);
    }
}
