package com.priceforecast.mapper;

import com.priceforecast.entity.AlertThreshold;
import com.priceforecast.entity.PriceAlert;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface AlertMapper {

    // ===== price_alert 告警记录 =====

    /** 查询某商品的告警记录（按时间倒序） */
    @Select("SELECT * FROM price_alert WHERE goods_id = #{goodsId} ORDER BY create_time DESC")
    List<PriceAlert> selectAlertsByGoods(@Param("goodsId") Long goodsId);

    /** 查询全部告警记录（按时间倒序） */
    @Select("SELECT * FROM price_alert ORDER BY create_time DESC")
    List<PriceAlert> selectAllAlerts();

    // ===== alert_threshold 阈值配置 =====

    /** 查询某商品的阈值配置 */
    @Select("SELECT * FROM alert_threshold WHERE goods_id = #{goodsId}")
    AlertThreshold selectThresholdByGoods(@Param("goodsId") Long goodsId);

    /** 查询全部阈值配置 */
    @Select("SELECT * FROM alert_threshold")
    List<AlertThreshold> selectAllThresholds();

    /** 插入阈值配置（无则插入） */
    @Insert("INSERT INTO alert_threshold (goods_id, up_threshold, down_threshold) " +
            "VALUES (#{goodsId}, #{upThreshold}, #{downThreshold})")
    int insertThreshold(AlertThreshold threshold);

    /** 更新阈值配置 */
    @Update("UPDATE alert_threshold SET up_threshold = #{upThreshold}, down_threshold = #{downThreshold}, " +
            "update_time = CURRENT_TIMESTAMP WHERE goods_id = #{goodsId}")
    int updateThreshold(AlertThreshold threshold);
}
