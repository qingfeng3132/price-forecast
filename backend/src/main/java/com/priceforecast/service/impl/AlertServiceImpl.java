package com.priceforecast.service.impl;

import com.priceforecast.entity.AlertThreshold;
import com.priceforecast.entity.PriceAlert;
import com.priceforecast.mapper.AlertMapper;
import com.priceforecast.service.AlertService;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AlertServiceImpl implements AlertService {

    private final AlertMapper alertMapper;

    // 构造器注入（遵循阿里巴巴Java开发手册）
    public AlertServiceImpl(AlertMapper alertMapper) {
        this.alertMapper = alertMapper;
    }

    @Override
    public List<PriceAlert> getAlertsByGoods(Long goodsId) {
        return alertMapper.selectAlertsByGoods(goodsId);
    }

    @Override
    public List<PriceAlert> getAllAlerts() {
        return alertMapper.selectAllAlerts();
    }

    @Override
    public AlertThreshold getThreshold(Long goodsId) {
        return alertMapper.selectThresholdByGoods(goodsId);
    }

    @Override
    public List<AlertThreshold> getAllThresholds() {
        return alertMapper.selectAllThresholds();
    }

    @Override
    public void saveThreshold(AlertThreshold threshold) {
        // 已存在则更新，不存在则插入
        AlertThreshold existing = alertMapper.selectThresholdByGoods(threshold.getGoodsId());
        if (existing == null) {
            alertMapper.insertThreshold(threshold);
        } else {
            alertMapper.updateThreshold(threshold);
        }
    }
}
