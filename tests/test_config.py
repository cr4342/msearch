"""
测试配置文件
专为测试环境设计的轻量级配置，避免模型依赖
"""

TEST_CONFIG = {
    "system": {
        "log_level": "INFO",
        "data_dir": "./tests/test_data",
        "temp_dir": "./tests/temp",
        "max_workers": 2
    },
    "database": {
        "sqlite": {
            "path": "./tests/test_data/test_msearch.db",
            "connection_pool_size": 5,
            "timeout": 10
        },
        "qdrant": {
            "host": "localhost",
            "port": 6333,
            "timeout": 10,
            "collections": {
                "visual_vectors": "test_visual_vectors",
                "audio_music_vectors": "test_audio_music_vectors", 
                "audio_speech_vectors": "test_audio_speech_vectors"
            }
        }
    },
    "infinity": {
        "services": {
            "clip": {
                "model_id": "mock/clip-model",
                "port": 17997,
                "device": "cpu",
                "max_batch_size": 8,
                "dtype": "float32"
            },
            "clap": {
                "model_id": "mock/clap-model", 
                "port": 17998,
                "device": "cpu",
                "max_batch_size": 4,
                "dtype": "float32"
            },
            "whisper": {
                "model_id": "mock/whisper-model",
                "port": 17999,
                "device": "cpu", 
                "max_batch_size": 2,
                "dtype": "float32"
            }
        },
        "health_check": {
            "interval": 5,
            "failure_threshold": 2,
            "timeout": 2
        },
        "resource_monitor": {
            "interval": 10,
            "gpu_threshold": 0.9,
            "memory_threshold": 0.85,
            "auto_cleanup": False
        }
    },
    "media_processing": {
        "video": {
            "max_resolution": 320,
            "target_fps": 4,
            "codec": "h264",
            "scene_detection": {
                "enabled": False,
                "threshold": 30.0,
                "min_scene_length": 30,
                "max_scene_length": 120
            }
        },
        "audio": {
            "sample_rate": 8000,
            "channels": 1,
            "bitrate": 32000,
            "codec": "aac",
            "quality_filter": {
                "min_duration": 1.0,
                "min_snr_ratio": 3.0,
                "enable_silence_detection": False
            }
        }
    },
    "face_recognition": {
        "enabled": False,  # 测试环境禁用人脸识别
        "model": "facenet",
        "detector": "mtcnn",
        "detection": {
            "min_face_size": 20,
            "confidence_threshold": 0.8,
            "nms_threshold": 0.3
        },
        "feature_extraction": {
            "vector_dim": 128,
            "normalize": True
        },
        "matching": {
            "similarity_threshold": 0.6,
            "enable_fuzzy_matching": True,
            "fuzzy_threshold": 0.8,
            "max_matches": 5
        },
        "indexing": {
            "video_sample_interval": 10,
            "batch_size": 8,
            "enable_clustering": False
        }
    },
    "smart_retrieval": {
        "default_weights": {
            "clip": 0.4,
            "clap": 0.3,
            "whisper": 0.3
        },
        "person_weights": {
            "clip": 0.5,
            "clap": 0.25,
            "whisper": 0.25
        },
        "audio_weights": {
            "music": {
                "clip": 0.2,
                "clap": 0.7,
                "whisper": 0.1
            },
            "speech": {
                "clip": 0.2,
                "clap": 0.1,
                "whisper": 0.7
            }
        },
        "visual_weights": {
            "clip": 0.7,
            "clap": 0.15,
            "whisper": 0.15
        },
        "keywords": {
            "music": ["音乐", "歌曲", "MV", "音乐视频", "歌", "曲子", "旋律", "节拍"],
            "speech": ["讲话", "演讲", "会议", "访谈", "对话", "发言", "语音"],
            "visual": ["画面", "场景", "图像", "图片", "视频画面", "截图"]
        }
    },
    "test_mode": True,  # 测试模式标志
    "mock_models": True  # 使用mock模型
}


def get_test_config():
    """获取测试配置"""
    return TEST_CONFIG


def patch_config_for_testing():
    """为测试环境修补配置"""
    import os
    # 设置测试环境变量
    os.environ["MSEARCH_TEST_MODE"] = "true"
    os.environ["MSEARCH_MOCK_MODELS"] = "true"
    os.environ["MSEARCH_DEVICE"] = "cpu"