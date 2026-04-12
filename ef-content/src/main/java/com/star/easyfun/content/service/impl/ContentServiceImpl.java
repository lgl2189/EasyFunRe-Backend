package com.star.easyfun.content.service.impl;

import com.star.easyfun.content.constant.PostConstant;
import com.star.easyfun.content.mapper.ContentPostMapper;
import com.star.easyfun.content.mapper.ContentPostResourceMapper;
import com.star.easyfun.content.mapper.ContentResourceMapper;
import com.star.easyfun.content.pojo.dbo.ContentPost;
import com.star.easyfun.content.pojo.dbo.ContentPostResource;
import com.star.easyfun.content.pojo.dbo.ContentResource;
import com.star.easyfun.content.pojo.dto.VideoPostDTO;
import com.star.easyfun.content.service.ContentService;
import com.star.easyfun.content.service.MinioService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.List;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 09 13:11
 */

@Service
@RequiredArgsConstructor
public class ContentServiceImpl implements ContentService {

    private final MinioService minioService;
    private final ContentPostMapper postMapper;
    private final ContentResourceMapper resourceMapper;
    private final ContentPostResourceMapper postResourceMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long uploadVideoPost(VideoPostDTO dto, Long ownerId) {

        // 1. 创建 ContentPost 主表
        ContentPost post = new ContentPost();
        post.setOwnerId(ownerId);
        post.setTitle(dto.getPostTitle());
        post.setDescription(dto.getPostDescription() != null ? dto.getPostDescription() : "");
        post.setPostType(dto.getIsMultiPart() ? 2 : 1);// 1=单视频，2=合集
        post.setIsVisibility(1);
        post.setAllowComment(1);
        post.setStatus(1);
        post.setViewCount(0);
        post.setLikeCount(0);
        //TODO: 评论区功能完成后补充在视频添加功能里
        post.setCommentCount(0);
        post.setCommentAreaId(0L);
        post.setCreatedAt(LocalDateTime.now());
        post.setUpdatedDatetime(LocalDateTime.now());

        // 2. 处理封面（取第一个）
        String coverKey;
        if (dto.getCoverList() != null && !dto.getCoverList().isEmpty()) {
            MultipartFile coverFile = dto.getCoverList().getFirst();
            try {
                coverKey = minioService.upload(coverFile, PostConstant.UPLOAD_POST_COVER_FOLDER);

                // 保存封面到 content_asset
                ContentResource coverAsset = buildContentAsset(coverFile, coverKey, 2, // 2=图片
                        dto.getPostTitle() + " 封面", ownerId);
                resourceMapper.insert(coverAsset);

                // 更新 post 的 coverUrl
                post.setCoverKey(coverKey);

            }
            catch (Exception e) {
                throw new RuntimeException("封面上传失败", e);
            }
        }
        postMapper.insert(post);
        Long postId = post.getPostId();

        // 3. 处理视频列表
        List<MultipartFile> videoFiles = dto.getVideoList();
        List<String> videoTitles = dto.getVideoTitleList();

        for (int i = 0; i < videoFiles.size(); i++) {
            MultipartFile videoFile = videoFiles.get(i);
            String videoTitle = (i < videoTitles.size()) ? videoTitles.get(i) : "视频" + (i + 1);

            try {
                // 上传到 MinIO video/ 目录
                String videoKey = minioService.upload(videoFile, PostConstant.UPLOAD_POST_VIDEO_FOLDER);

                // 保存视频到 content_asset
                ContentResource videoAsset = buildContentAsset(videoFile, videoKey, 1, // 1=视频
                        videoTitle, ownerId);
                // 可选：这里可以调用 FFmpeg 获取时长 duration（后面再加）
                resourceMapper.insert(videoAsset);

                // 建立投稿与资源的关联
                ContentPostResource relation = new ContentPostResource();
                relation.setPostId(postId);
                relation.setResourceId(videoAsset.getResourceId());
                relation.setSortOrder(i + 1);
                relation.setCreatedDatetime(LocalDateTime.now());
                relation.setUpdatedDatetime(LocalDateTime.now());
                postResourceMapper.insert(relation);

            }
            catch (Exception e) {
                throw new RuntimeException("视频上传失败", e);
            }
        }

        return postId;
    }

    @Override
    public String getVideoPlayUrl(Long postId) throws Exception {
        // TODO: 这里应该根据 postId 找到合适的视频资源，然后返回播放链接，暂时使用固定资源
        return minioService.getPresignedGetUrl("post/video/test-long.mp4");
    }

    /**
     * 辅助方法：构建 ContentResource
     */
    private ContentResource buildContentAsset(MultipartFile file, String fileKey,
                                              Integer assetType, String title, Long ownerId) {
        ContentResource asset = new ContentResource();
        asset.setResourceType(assetType);
        asset.setTitle(title);
        asset.setDescription("");
        asset.setFileKey(fileKey);
        asset.setFileSize(file.getSize());
        asset.setFileType(file.getContentType());
        asset.setStatus(1);
        asset.setOwnerId(ownerId);
        asset.setCreatedDatetime(LocalDateTime.now());
        asset.setUpdatedDatetime(LocalDateTime.now());
        return asset;
    }
}