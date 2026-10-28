package com.priceforecast.service.impl;


import com.priceforecast.entity.Goods;
import com.priceforecast.mapper.GoodsMapper;
import com.priceforecast.service.GoodsService;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class GoodsServiceImpl implements GoodsService {
    private final GoodsMapper goodsMapper;

    public GoodsServiceImpl(GoodsMapper goodsMapper){
        this.goodsMapper=goodsMapper;
    }
    @Override
    public Goods getById(Long id){
        return goodsMapper.selectById(id);

    }
    @Override
    public List<Goods> listAll(){
        return goodsMapper.selectAll();

    }


}
