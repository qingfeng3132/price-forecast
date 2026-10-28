package com.priceforecast.service;

import com.priceforecast.entity.Goods;

import java.util.List;

public interface GoodsService {
    Goods getById(Long id);

    List<Goods>listAll();

}
