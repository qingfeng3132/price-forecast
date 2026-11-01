package com.priceforecast.controller;

import com.priceforecast.service.PriceDataService;
import com.priceforecast.entity.PriceData;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
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

    /**
     * 入库接口：爬虫 POST 价格数据列表过来，后端写入数据库
     * 请求体形如：[{"goodsId":4,"price":16.06,"priceUnit":"元/公斤","region":"国家级","priceDate":"2026-10-14"}]
     */
    @PostMapping("/import")
    public Map<String, Object> importData(@RequestBody List<PriceData> list) {
        int count = priceDataService.batchInsert(list);
        return Map.of("code", 200, "message", "成功", "count", count);
    }
}
