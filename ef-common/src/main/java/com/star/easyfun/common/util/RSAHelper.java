package com.star.easyfun.common.util;

import com.star.easyfun.common.config.property.jwt.JWTProperty;
import com.star.easyfun.common.pojo.entity.CustomRSAKeyPair;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.security.*;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

/**
 * @author ：Star
 * @description ：    RSA相关的工具方法
 * @date ：2026 3月 01 21:49
 */

@Component
@RequiredArgsConstructor
public class RSAHelper {
    private final JWTProperty jwtProperty;

    /**
     * 从nacos配置中心获取RSA密钥对
     *
     * @return RSA密钥对
     * @throws Exception 获取密钥对失败
     */
    public CustomRSAKeyPair getRSAKeyPair() throws Exception {
        return new CustomRSAKeyPair(getPublicKey(), getPrivateKey(), jwtProperty.getRsa().getKeyId());
    }

    // 获取公钥对象
    public PublicKey getPublicKey() throws Exception {
        String key = jwtProperty.getRsa().getPublicKey()
                .replace("-----BEGIN PUBLIC KEY-----", "")
                .replace("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s", ""); // 去除所有空白字符
        byte[] keyBytes = Base64.getDecoder().decode(key);
        X509EncodedKeySpec keySpec = new X509EncodedKeySpec(keyBytes);
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");
        return keyFactory.generatePublic(keySpec);
    }

    // 获取私钥对象
    public PrivateKey getPrivateKey() throws Exception {
        String key = jwtProperty.getRsa().getPrivateKey()
                .replace("-----BEGIN PRIVATE KEY-----", "")
                .replace("-----END PRIVATE KEY-----", "")
                .replaceAll("\\s", "");
        byte[] keyBytes = Base64.getDecoder().decode(key);
        PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(keyBytes);
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");
        return keyFactory.generatePrivate(keySpec);
    }

    public static KeyPair generateRSAKeyPair(int keySize) {
        // 生成并返回RSA密钥对（包含随机生成的公钥和私钥）
        try {
            KeyPairGenerator keyPairGenerator = KeyPairGenerator.getInstance("RSA");
            // 初始化密钥长度为2048位（推荐2048/4096，1024已不安全；长度越长加密强度越高，但性能略降）
            keyPairGenerator.initialize(keySize);
            return keyPairGenerator.generateKeyPair();
        }
        catch (Exception e) {
            throw new RuntimeException("生成RSA密钥对失败", e);
        }
    }

    /**
     * 将 RSA 公钥编码为 Base64 字符串
     * 注：默认使用 X.509 标准格式编码公钥
     */
    public String getPublicKeyBase64String() {
        // 1. 获取公钥的二进制编码（X.509 格式）
        // 2. 使用 Java 8+ 标准 Base64 编码器编码为字符串
        return Base64.getEncoder().encodeToString(jwtProperty.getRsa().getPublicKey().getBytes());
    }
}