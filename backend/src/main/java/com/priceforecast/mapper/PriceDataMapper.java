package com.priceforecast.mapper;

import com.priceforecast.entity.PriceData;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDate;
import java.util.List;

@Mapper
public interface PriceDataMapper {
    @Select("SELECT * FROM price_data " + "WHERE goods_id = #{goodsId} " + "AND price_date >= #{startDate} " + "AND price_date <= #{endDate} " + "ORDER BY price_date ASC")
    List<PriceData> selectByGoodsAndDateRange(
            @Param("goodsId") Long goodsId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);


}
