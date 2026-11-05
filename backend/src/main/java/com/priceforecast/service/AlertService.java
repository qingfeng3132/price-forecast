package com.priceforecast.service;

import com.priceforecast.entity.AlertThreshold;
import com.priceforecast.entity.PriceAlert;

import java.util.List;

public interface AlertService {

    /** 查询某商品的告警记录 */
    List<PriceAlert> getAlertsByGoods(Long goodsId);

    /** 查询全部告警记录 */
    List<PriceAlert> getAllAlerts();

    /** 查询某商品的阈值配置 */
    AlertThreshold getThreshold(Long goodsId);

    /** 查询全部阈值配置 */
    List<AlertThreshold> getAllThresholds();

    /**
     * 保存（新增或更新）某商品的阈值配置
     * 已存在则更新，不存在则插入
     */
    void saveThreshold(AlertThreshold threshold);
}
