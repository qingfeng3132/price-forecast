package com.priceforecast.controller;

import com.priceforecast.entity.Goods;
import com.priceforecast.service.GoodsService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


import java.util.List;

@RestController
@RequestMapping("/api/goods")
public class GoodsController {
    private final GoodsService goodsService;

    public GoodsController(GoodsService goodsService){
        this.goodsService=goodsService;

    }
    @GetMapping("/{id}")
    public Goods getById(@PathVariable Long id){
        return goodsService.getById(id);
    }
    @GetMapping
    public List<Goods> listAll(){
        return goodsService.listAll();
    }

}
