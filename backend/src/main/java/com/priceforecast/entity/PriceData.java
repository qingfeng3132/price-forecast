package com.priceforecast.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class PriceData {
    private Long id;
    private Long goodsId;
    private BigDecimal price;
    private String priceUnit;
    private LocalDate priceDate;
    private BigDecimal changeRate;
    private String sourceUrl;
    private LocalDateTime crawlTime;
}
