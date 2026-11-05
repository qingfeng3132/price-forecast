package com.priceforecast.controller;

import com.priceforecast.entity.AlertThreshold;
import com.priceforecast.entity.PriceAlert;
import com.priceforecast.service.AlertService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/alert")
public class AlertController {

    private final AlertService alertService;

    public AlertController(AlertService alertService) {
        this.alertService = alertService;
    }

    /**
     * 查询告警记录
     * GET /api/alert             -> 全部告警
     * GET /api/alert?goodsId=4   -> 某商品的告警
     */
    @GetMapping
    public List<PriceAlert> getAlerts(@RequestParam(required = false) Long goodsId) {
        if (goodsId == null) {
            return alertService.getAllAlerts();
        }
        return alertService.getAlertsByGoods(goodsId);
    }

    /**
     * 查询阈值配置
     * GET /api/alert/threshold             -> 全部阈值
     * GET /api/alert/threshold?goodsId=4   -> 某商品阈值
     */
    @GetMapping("/threshold")
    public Object getThreshold(@RequestParam(required = false) Long goodsId) {
        if (goodsId == null) {
            return alertService.getAllThresholds();
        }
        return alertService.getThreshold(goodsId);
    }

    /**
     * 保存（新增/更新）阈值配置
     * POST /api/alert/threshold
     * 请求体：{"goodsId":4, "upThreshold":15, "downThreshold":10}
     */
    @PostMapping("/threshold")
    public Map<String, Object> saveThreshold(@RequestBody AlertThreshold threshold) {
        alertService.saveThreshold(threshold);
        return Map.of("code", 200, "message", "成功");
    }
}
