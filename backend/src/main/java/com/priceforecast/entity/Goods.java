package com.priceforecast.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class Goods {
    private Long id;
    private String goodsCode;
    private String goodsName;
    private Long categoryId;
    private String sourcePlatform;
    private String updateFrequency;
    private LocalDateTime createTime;

}
