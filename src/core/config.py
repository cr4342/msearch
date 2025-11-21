"""
配置类定义
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class SystemConfig:
    """系统配置"""
    log_level: str = "INFO"
    data_dir: str = "./data"
    temp_dir: str = "./temp"
    monitored_directories: List[str] = None
    supported_extensions: List[str] = None
    debounce_delay: float = 0.5
    max_workers: int = 4
    
    def __post_init__(self):
        if self.monitored_directories is None:
            self.monitored_directories = ["./data/media"]
        if self.supported_extensions is None:
            self.supported_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.mp4', '.avi', '.mov', '.mp3', '.wav', '.flac']


@dataclass
class DatabaseConfig:
    """数据库配置"""
    sqlite_path: str = "./data/msearch.db"
    connection_pool_size: int = 10
    timeout: int = 30


@dataclass
class QdrantConfig:
    """Qdrant配置"""
    host: str = "localhost"
    port: int = 6333
    timeout: int = 30
    collections: Dict[str, str] = None
    
    def __post_init__(self):
        if self.collections is None:
            self.collections = {
                "visual_vectors": "visual_vectors",
                "audio_music_vectors": "audio_music_vectors",
                "audio_speech_vectors": "audio_speech_vectors"
            }


@dataclass
class ModelConfig:
    """模型配置"""
    model_id: str
    port: int
    device: str = "cuda:0"
    max_batch_size: int = 32
    dtype: str = "float16"


@dataclass
class InfinityConfig:
    """Infinity配置"""
    services: Dict[str, ModelConfig] = None
    health_check: Dict[str, Any] = None
    resource_monitor: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.services is None:
            self.services = {
                "clip": ModelConfig("openai/clip-vit-base-patch32", 7997),
                "clap": ModelConfig("laion/clap-htsat-fused", 7998),
                "whisper": ModelConfig("openai/whisper-base", 7999)
            }
        
        if self.health_check is None:
            self.health_check = {
                "interval": 30,
                "failure_threshold": 3,
                "timeout": 5
            }
        
        if self.resource_monitor is None:
            self.resource_monitor = {
                "interval": 60,
                "gpu_threshold": 0.9,
                "memory_threshold": 0.85,
                "auto_cleanup": True
            }


@dataclass
class VideoProcessingConfig:
    """视频处理配置"""
    max_resolution: int = 960
    target_fps: int = 8
    codec: str = "h264"
    scene_detection: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.scene_detection is None:
            self.scene_detection = {
                "enabled": True,
                "threshold": 30.0,
                "min_scene_length": 30,
                "max_scene_length": 120
            }


@dataclass
class AudioProcessingConfig:
    """音频处理配置"""
    sample_rate: int = 16000
    channels: int = 1
    bitrate: int = 64000
    codec: str = "aac"
    quality_filter: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.quality_filter is None:
            self.quality_filter = {
                "min_duration": 3.0,
                "min_snr_ratio": 5.0,
                "enable_silence_detection": True
            }


@dataclass
class MediaProcessingConfig:
    """媒体处理配置"""
    video: VideoProcessingConfig = None
    audio: AudioProcessingConfig = None
    
    def __post_init__(self):
        if self.video is None:
            self.video = VideoProcessingConfig()
        if self.audio is None:
            self.audio = AudioProcessingConfig()


@dataclass
class FaceDetectionConfig:
    """人脸检测配置"""
    min_face_size: int = 40
    confidence_threshold: float = 0.9
    nms_threshold: float = 0.4


@dataclass
class FaceFeatureConfig:
    """人脸特征配置"""
    vector_dim: int = 512
    normalize: bool = True


@dataclass
class FaceMatchingConfig:
    """人脸匹配配置"""
    similarity_threshold: float = 0.6
    enable_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.8
    max_matches: int = 10


@dataclass
class FaceIndexingConfig:
    """人脸索引配置"""
    video_sample_interval: int = 5
    batch_size: int = 16
    enable_clustering: bool = False


@dataclass
class FaceRecognitionConfig:
    """人脸识别配置"""
    enabled: bool = True
    model: str = "facenet"
    detector: str = "mtcnn"
    detection: FaceDetectionConfig = None
    feature_extraction: FaceFeatureConfig = None
    matching: FaceMatchingConfig = None
    indexing: FaceIndexingConfig = None
    
    def __post_init__(self):
        if self.detection is None:
            self.detection = FaceDetectionConfig()
        if self.feature_extraction is None:
            self.feature_extraction = FaceFeatureConfig()
        if self.matching is None:
            self.matching = FaceMatchingConfig()
        if self.indexing is None:
            self.indexing = FaceIndexingConfig()


@dataclass
class RetrievalWeights:
    """检索权重配置"""
    clip: float = 0.4
    clap: float = 0.3
    whisper: float = 0.3


@dataclass
class SmartRetrievalConfig:
    """智能检索配置"""
    default_weights: RetrievalWeights = None
    person_weights: RetrievalWeights = None
    audio_weights: Dict[str, RetrievalWeights] = None
    visual_weights: RetrievalWeights = None
    keywords: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.default_weights is None:
            self.default_weights = RetrievalWeights()
        
        if self.person_weights is None:
            self.person_weights = RetrievalWeights(
                clip=0.5, clap=0.25, whisper=0.25
            )
        
        if self.audio_weights is None:
            self.audio_weights = {
                "music": RetrievalWeights(clip=0.2, clap=0.7, whisper=0.1),
                "speech": RetrievalWeights(clip=0.2, clap=0.1, whisper=0.7)
            }
        
        if self.visual_weights is None:
            self.visual_weights = RetrievalWeights(
                clip=0.7, clap=0.15, whisper=0.15
            )
        
        if self.keywords is None:
            self.keywords = {
                "music": ["音乐", "歌曲", "MV", "音乐视频", "歌", "曲子", "旋律", "节拍"],
                "speech": ["讲话", "演讲", "会议", "访谈", "对话", "发言", "语音"],
                "visual": ["画面", "场景", "图像", "图片", "视频画面", "截图"]
            }


@dataclass
class DatabaseConfig:
    """数据库配置"""
    sqlite: DatabaseConfig = None
    qdrant: QdrantConfig = None
    
    def __post_init__(self):
        if self.sqlite is None:
            self.sqlite = DatabaseConfig()
        if self.qdrant is None:
            self.qdrant = QdrantConfig()


@dataclass
class OrchestratorConfig:
    """调度器配置"""
    check_interval: float = 5.0
    max_concurrent_tasks: int = 3


@dataclass
class TaskManagerConfig:
    """任务管理器配置"""
    max_retry_attempts: int = 3
    retry_delay: int = 60
    task_timeout: int = 3600


@dataclass
class MSearchConfig:
    """msearch主配置"""
    system: SystemConfig = None
    database: DatabaseConfig = None
    infinity: InfinityConfig = None
    media_processing: MediaProcessingConfig = None
    face_recognition: FaceRecognitionConfig = None
    smart_retrieval: SmartRetrievalConfig = None
    orchestrator: OrchestratorConfig = None
    task_manager: TaskManagerConfig = None
    
    def __post_init__(self):
        if self.system is None:
            self.system = SystemConfig()
        if self.database is None:
            self.database = DatabaseConfig()
        if self.infinity is None:
            self.infinity = InfinityConfig()
        if self.media_processing is None:
            self.media_processing = MediaProcessingConfig()
        if self.face_recognition is None:
            self.face_recognition = FaceRecognitionConfig()
        if self.smart_retrieval is None:
            self.smart_retrieval = SmartRetrievalConfig()
        if self.orchestrator is None:
            self.orchestrator = OrchestratorConfig()
        if self.task_manager is None:
            self.task_manager = TaskManagerConfig()