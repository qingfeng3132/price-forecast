package com.priceforecast;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.mybatis.spring.annotation.MapperScan;

@SpringBootApplication
@MapperScan("com.priceforecast.mapper")
public class PriceForecastApplication {

	public static void main(String[] args) {
		SpringApplication.run(PriceForecastApplication.class, args);
	}

}
