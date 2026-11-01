package com.priceforecast.mapper;

import com.priceforecast.entity.Forecast;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface ForecastMapper {

    /**
     * 查询某商品最新一次预测（未来 7 天），按预测日期升序
     * 取 model_name='ARIMA' 且 forecast_date 在最近一次预测批次内的记录
     */
    @Select("SELECT * FROM forecast WHERE goods_id = #{goodsId} AND model_name = #{modelName} " +
            "ORDER BY forecast_date ASC")
    List<Forecast> selectByGoodsAndModel(
            @Param("goodsId") Long goodsId,
            @Param("modelName") String modelName);

    /**
     * 查询某商品某模型下，预测日期 >= 指定日期的预测（用于拿未来 7 天）
     */
    @Select("SELECT * FROM forecast WHERE goods_id = #{goodsId} AND model_name = #{modelName} " +
            "AND forecast_date >= #{startDate} ORDER BY forecast_date ASC")
    List<Forecast> selectFuture(
            @Param("goodsId") Long goodsId,
            @Param("modelName") String modelName,
            @Param("startDate") java.time.LocalDate startDate);
}
