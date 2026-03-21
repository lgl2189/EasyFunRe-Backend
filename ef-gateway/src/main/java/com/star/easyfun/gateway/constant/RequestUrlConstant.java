package com.star.easyfun.gateway.constant;

/**
 * @author ：Star
 * @description ：用于存放请求地址的常量类
 * @date ：2025 11月 16 23:20
 */


public class RequestUrlConstant {
    public static final String[] gatewaySecurityIgnoreUrlList = {
            "/auth/login/sms",
            "/auth/login/password",
            // token登录是借由AuthFilter处理的，所以这里不需要忽略token登录的url
            "/auth/refresh/token"
    };
}