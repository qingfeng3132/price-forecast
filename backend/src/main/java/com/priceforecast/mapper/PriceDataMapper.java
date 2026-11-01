package com.priceforecast.mapper;

import com.priceforecast.entity.PriceData;
import org.apache.ibatis.annotations.Insert;
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

    /**
     * 插入一条价格数据，重复(goods_id + price_date)则更新价格，实现幂等
     * 任务书要求"去重"，这里用 MySQL 的 ON DUPLICATE KEY UPDATE 兜底
     */
    @Insert("INSERT INTO price_data (goods_id, price, price_unit, region, price_date, source_url) " +
            "VALUES (#{goodsId}, #{price}, #{priceUnit}, #{region}, #{priceDate}, #{sourceUrl}) " +
            "ON DUPLICATE KEY UPDATE price = VALUES(price), price_unit = VALUES(price_unit), region = VALUES(region)")
    int insert(PriceData priceData);
}
