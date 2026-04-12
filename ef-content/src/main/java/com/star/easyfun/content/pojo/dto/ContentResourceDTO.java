package com.star.easyfun.content.pojo.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;

/**
 * @author ：Star
 * @description ：    表示一个资源的所有信息
 * @date ：2026 4月 12 14:47
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class ContentResourceDTO {
    private Long resourceId;
    /**
     * 内容类型：1=视频，2=图片，3=音频，4=文本，5=其他
     */
    private Integer resourceType;
    /**
     * 内容的标题
     */
    private String title;
    /**
     * 内容的简介
     */
    private String description;
    /**
     * Minio预签名下载URL
     */
    private String fileUrl;
    /**
     * 云存储原始key
     */
    private String fileKey;
    /**
     * 文件大小，单位为字节
     */
    private Long fileSize;
    /**
     * 时长，仅视频、音频有效（单位：秒）
     */
    private Integer duration;
    /**
     * 图片宽度，仅图片有效
     */
    private Integer width;
    /**
     * 图片高度，仅图片有效
     */
    private Integer height;
    /**
     * 内容对应的文件本身的类型
     */
    private String fileType;
    /**
     * 内容状态：1=正常，0=已删除
     */
    private Integer status;
    /**
     * 内容拥有者的ID，即上传者
     */
    private Long ownerId;
    /**
     * 排序序号（同一个投稿内内容的显示顺序，从小到大）
     */
    private Integer sortOrder;
    /**
     * 内容的创建时间
     */
    private LocalDateTime createdDatetime;
    /**
     * 内容的更新时间（需手动维护）
     */
    private LocalDateTime updatedDatetime;
}