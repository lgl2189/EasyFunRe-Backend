package com.star.easyfun.content.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.star.easyfun.content.constant.PostConstant;
import com.star.easyfun.content.mapper.ContentPostMapper;
import com.star.easyfun.content.mapper.ContentPostResourceMapper;
import com.star.easyfun.content.mapper.ContentResourceMapper;
import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
import com.star.easyfun.content.pojo.dbo.ContentPostResourceDBO;
import com.star.easyfun.content.pojo.dbo.ContentResourceDBO;
import com.star.easyfun.content.pojo.dto.ContentPostDTO;
import com.star.easyfun.content.pojo.dto.ContentResourceDTO;
import com.star.easyfun.content.pojo.dto.VideoPostUploadDTO;
import com.star.easyfun.content.pojo.mapper.PostStructMapper;
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

    private final PostStructMapper postStructMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long uploadVideoPost(VideoPostUploadDTO dto, Long ownerId) {

        // 1. 创建 ContentPostDBO 主表
        ContentPostDBO post = new ContentPostDBO();
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
        post.setPublishedAt(LocalDateTime.now());
        post.setUpdatedDatetime(LocalDateTime.now());

        // 2. 处理封面（取第一个）
        String coverKey;
        if (dto.getCoverList() != null && !dto.getCoverList().isEmpty()) {
            MultipartFile coverFile = dto.getCoverList().getFirst();
            try {
                coverKey = minioService.upload(coverFile, PostConstant.UPLOAD_POST_COVER_FOLDER);

                // 保存封面到 content_asset
                ContentResourceDBO coverAsset = buildContentAsset(coverFile, coverKey, 2, // 2=图片
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
                ContentResourceDBO videoAsset = buildContentAsset(videoFile, videoKey, 1, // 1=视频
                        videoTitle, ownerId);
                // 可选：这里可以调用 FFmpeg 获取时长 duration（后面再加）
                resourceMapper.insert(videoAsset);

                // 建立投稿与资源的关联
                ContentPostResourceDBO relation = new ContentPostResourceDBO();
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
    public ContentPostDTO getPost(Long postId) throws Exception {
        ContentPostDBO contentPostDBO = postMapper.selectById(postId);
        LambdaQueryWrapper<ContentPostResourceDBO> resourceListWrapper = new LambdaQueryWrapper<>();
        resourceListWrapper.eq(ContentPostResourceDBO::getPostId, postId);
        List<ContentResourceDTO> resourceDTOList = postMapper.selectResourceList(postId);
        for(ContentResourceDTO resourceDTO: resourceDTOList){
            resourceDTO.setFileUrl(minioService.getPresignedGetUrl(resourceDTO.getFileKey()));
        }
        ContentPostDTO contentPostDTO = postStructMapper.fromPostDBO(contentPostDBO);
        contentPostDTO.setCoverUrl(minioService.getPresignedGetUrl(contentPostDTO.getCoverKey()));
        contentPostDTO.setResourceList(resourceDTOList);
        return contentPostDTO;
    }

    /**
     * 辅助方法：构建 ContentResourceDBO
     */
    private ContentResourceDBO buildContentAsset(MultipartFile file, String fileKey,
                                                 Integer assetType, String title, Long ownerId) {
        ContentResourceDBO asset = new ContentResourceDBO();
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