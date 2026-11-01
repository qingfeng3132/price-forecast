package com.priceforecast.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class Forecast {
    private Long id;
    private Long goodsId;
    private LocalDate forecastDate;
    private BigDecimal forecastPrice;
    private String modelName;
    private BigDecimal confidence;
    private String basisSummary;
    private LocalDateTime createTime;
}
