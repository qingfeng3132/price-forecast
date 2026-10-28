package com.priceforecast.mapper;


import com.priceforecast.entity.Goods;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;


@Mapper
public interface GoodsMapper {
    @Select("SELECT * FROM goods WHERE id =#{id}")
    Goods selectById (long id);


    @Select("SELECT * FROM goods")
    List<Goods>selectAll();
}
