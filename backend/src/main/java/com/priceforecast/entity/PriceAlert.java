package com.priceforecast.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class PriceAlert {
    private Long id;
    private Long goodsId;
    private String alertType;
    private BigDecimal changeRate;
    private BigDecimal threshold;
    private String alertStatus;
    private String notifyChannel;
    private String notifyStatus;
    private LocalDate alertDate;
    private LocalDateTime createTime;
    private LocalDateTime handleTime;
}
