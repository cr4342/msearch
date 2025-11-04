"""
时间戳数据库管理器 - 管理视频和音频的时间戳索引
实现±2秒精度的时间戳存储和查询
"""
import sqlite3
import json
from typing import Dict, Any, List, Optional, Tuple
import logging
from pathlib import Path
from dataclasses import asdict

from src.processors.timestamp_processor import TimestampInfo, ModalityType

logger = logging.getLogger(__name__)


class TimestampDatabase:
    """时间戳数据库管理器"""
    
    def __init__(self, db_path: str):
        """
        初始化时间戳数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection = None
        self._init_database()
        
        logger.info(f"时间戳数据库初始化完成: {db_path}")
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            # 确保数据库目录存在
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 连接数据库
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # 启用字典式访问
            
            # 创建时间戳索引表
            self._create_timestamp_table()
            
            # 创建索引以优化查询性能
            self._create_indexes()
            
            logger.info("时间戳数据库表结构初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _create_timestamp_table(self):
        """创建时间戳索引表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS video_timestamps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            vector_id TEXT,
            segment_id TEXT NOT NULL,
            modality TEXT NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            duration REAL NOT NULL,
            frame_index INTEGER,
            confidence REAL DEFAULT 1.0,
            scene_boundary BOOLEAN DEFAULT FALSE,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        self.connection.execute(create_table_sql)
        self.connection.commit()
    
    def _create_indexes(self):
        """创建查询优化索引"""
        indexes = [
            # 时间范围查询索引
            "CREATE INDEX IF NOT EXISTS idx_time_range ON video_timestamps(file_id, start_time, end_time);",
            # 向量ID查询索引
            "CREATE INDEX IF NOT EXISTS idx_vector_lookup ON video_timestamps(vector_id);",
            # 模态时间索引
            "CREATE INDEX IF NOT EXISTS idx_modality_time ON video_timestamps(modality, start_time);",
            # 文件ID索引
            "CREATE INDEX IF NOT EXISTS idx_file_id ON video_timestamps(file_id);",
            # 段ID索引
            "CREATE INDEX IF NOT EXISTS idx_segment_id ON video_timestamps(segment_id);",
            # 场景边界索引
            "CREATE INDEX IF NOT EXISTS idx_scene_boundary ON video_timestamps(scene_boundary, file_id);"
        ]
        
        for index_sql in indexes:
            self.connection.execute(index_sql)
        
        self.connection.commit()
        logger.debug("数据库索引创建完成")
    
    def insert_timestamp_info(self, timestamp_info: TimestampInfo) -> int:
        """
        插入时间戳信息
        
        Args:
            timestamp_info: 时间戳信息对象
            
        Returns:
            插入记录的ID
        """
        try:
            insert_sql = """
            INSERT INTO video_timestamps (
                file_id, vector_id, segment_id, modality, start_time, end_time, 
                duration, frame_index, confidence, scene_boundary, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # 准备元数据JSON
            metadata_json = json.dumps({
                'modality_type': timestamp_info.modality.value,
                'processing_info': {
                    'accuracy_validated': True,
                    'sync_corrected': True
                }
            })
            
            cursor = self.connection.execute(insert_sql, (
                timestamp_info.file_id,
                timestamp_info.vector_id,
                timestamp_info.segment_id,
                timestamp_info.modality.value,
                timestamp_info.start_time,
                timestamp_info.end_time,
                timestamp_info.duration,
                timestamp_info.frame_index,
                timestamp_info.confidence,
                timestamp_info.scene_boundary,
                metadata_json
            ))
            
            self.connection.commit()
            
            record_id = cursor.lastrowid
            logger.debug(f"时间戳信息插入成功: ID={record_id}, segment_id={timestamp_info.segment_id}")
            
            return record_id
            
        except Exception as e:
            logger.error(f"时间戳信息插入失败: {e}")
            self.connection.rollback()
            raise
    
    def batch_insert_timestamp_infos(self, timestamp_infos: List[TimestampInfo]) -> List[int]:
        """
        批量插入时间戳信息
        
        Args:
            timestamp_infos: 时间戳信息列表
            
        Returns:
            插入记录的ID列表
        """
        try:
            insert_sql = """
            INSERT INTO video_timestamps (
                file_id, vector_id, segment_id, modality, start_time, end_time, 
                duration, frame_index, confidence, scene_boundary, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # 准备批量插入数据
            batch_data = []
            for ts_info in timestamp_infos:
                metadata_json = json.dumps({
                    'modality_type': ts_info.modality.value,
                    'processing_info': {
                        'accuracy_validated': True,
                        'sync_corrected': True
                    }
                })
                
                batch_data.append((
                    ts_info.file_id,
                    ts_info.vector_id,
                    ts_info.segment_id,
                    ts_info.modality.value,
                    ts_info.start_time,
                    ts_info.end_time,
                    ts_info.duration,
                    ts_info.frame_index,
                    ts_info.confidence,
                    ts_info.scene_boundary,
                    metadata_json
                ))
            
            # 执行批量插入
            cursor = self.connection.executemany(insert_sql, batch_data)
            self.connection.commit()
            
            # 获取插入的ID范围
            last_id = cursor.lastrowid
            first_id = last_id - len(timestamp_infos) + 1
            record_ids = list(range(first_id, last_id + 1))
            
            logger.info(f"批量插入时间戳信息成功: {len(timestamp_infos)}条记录")
            
            return record_ids
            
        except Exception as e:
            logger.error(f"批量插入时间戳信息失败: {e}")
            self.connection.rollback()
            raise
    
    def get_timestamp_info_by_vector_id(self, vector_id: str) -> Optional[TimestampInfo]:
        """
        根据向量ID获取时间戳信息
        
        Args:
            vector_id: 向量ID
            
        Returns:
            时间戳信息对象或None
        """
        try:
            query_sql = """
            SELECT * FROM video_timestamps 
            WHERE vector_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """
            
            cursor = self.connection.execute(query_sql, (vector_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_timestamp_info(row)
            
            return None
            
        except Exception as e:
            logger.error(f"根据向量ID查询时间戳信息失败: {e}")
            return None
    
    def get_timestamp_infos_by_file_id(self, file_id: str, 
                                      modality: Optional[ModalityType] = None) -> List[TimestampInfo]:
        """
        根据文件ID获取时间戳信息列表
        
        Args:
            file_id: 文件ID
            modality: 可选的模态类型过滤
            
        Returns:
            时间戳信息列表
        """
        try:
            if modality:
                query_sql = """
                SELECT * FROM video_timestamps 
                WHERE file_id = ? AND modality = ?
                ORDER BY start_time ASC
                """
                cursor = self.connection.execute(query_sql, (file_id, modality.value))
            else:
                query_sql = """
                SELECT * FROM video_timestamps 
                WHERE file_id = ?
                ORDER BY start_time ASC
                """
                cursor = self.connection.execute(query_sql, (file_id,))
            
            rows = cursor.fetchall()
            
            timestamp_infos = []
            for row in rows:
                ts_info = self._row_to_timestamp_info(row)
                if ts_info:
                    timestamp_infos.append(ts_info)
            
            logger.debug(f"查询到{len(timestamp_infos)}条时间戳信息: file_id={file_id}")
            
            return timestamp_infos
            
        except Exception as e:
            logger.error(f"根据文件ID查询时间戳信息失败: {e}")
            return []
    
    def get_timestamp_infos_by_time_range(self, file_id: str, start_time: float, 
                                         end_time: float, 
                                         modality: Optional[ModalityType] = None) -> List[TimestampInfo]:
        """
        根据时间范围获取时间戳信息
        
        Args:
            file_id: 文件ID
            start_time: 开始时间
            end_time: 结束时间
            modality: 可选的模态类型过滤
            
        Returns:
            时间戳信息列表
        """
        try:
            if modality:
                query_sql = """
                SELECT * FROM video_timestamps 
                WHERE file_id = ? AND modality = ?
                AND (
                    (start_time <= ? AND end_time >= ?) OR
                    (start_time >= ? AND start_time <= ?) OR
                    (end_time >= ? AND end_time <= ?)
                )
                ORDER BY start_time ASC
                """
                cursor = self.connection.execute(query_sql, (
                    file_id, modality.value,
                    end_time, start_time,  # 重叠检测
                    start_time, end_time,  # 开始时间在范围内
                    start_time, end_time   # 结束时间在范围内
                ))
            else:
                query_sql = """
                SELECT * FROM video_timestamps 
                WHERE file_id = ?
                AND (
                    (start_time <= ? AND end_time >= ?) OR
                    (start_time >= ? AND start_time <= ?) OR
                    (end_time >= ? AND end_time <= ?)
                )
                ORDER BY start_time ASC
                """
                cursor = self.connection.execute(query_sql, (
                    file_id,
                    end_time, start_time,  # 重叠检测
                    start_time, end_time,  # 开始时间在范围内
                    start_time, end_time   # 结束时间在范围内
                ))
            
            rows = cursor.fetchall()
            
            timestamp_infos = []
            for row in rows:
                ts_info = self._row_to_timestamp_info(row)
                if ts_info:
                    timestamp_infos.append(ts_info)
            
            logger.debug(f"时间范围查询到{len(timestamp_infos)}条记录: "
                        f"file_id={file_id}, time_range=[{start_time}, {end_time}]")
            
            return timestamp_infos
            
        except Exception as e:
            logger.error(f"时间范围查询失败: {e}")
            return []
    
    def update_vector_id(self, segment_id: str, vector_id: str) -> bool:
        """
        更新时间戳记录的向量ID
        
        Args:
            segment_id: 段ID
            vector_id: 向量ID
            
        Returns:
            更新是否成功
        """
        try:
            update_sql = """
            UPDATE video_timestamps 
            SET vector_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE segment_id = ?
            """
            
            cursor = self.connection.execute(update_sql, (vector_id, segment_id))
            self.connection.commit()
            
            updated_rows = cursor.rowcount
            
            if updated_rows > 0:
                logger.debug(f"向量ID更新成功: segment_id={segment_id}, vector_id={vector_id}")
                return True
            else:
                logger.warning(f"未找到要更新的记录: segment_id={segment_id}")
                return False
                
        except Exception as e:
            logger.error(f"向量ID更新失败: {e}")
            self.connection.rollback()
            return False
    
    def delete_timestamp_infos_by_file_id(self, file_id: str) -> int:
        """
        删除指定文件的所有时间戳信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            删除的记录数
        """
        try:
            delete_sql = "DELETE FROM video_timestamps WHERE file_id = ?"
            
            cursor = self.connection.execute(delete_sql, (file_id,))
            self.connection.commit()
            
            deleted_rows = cursor.rowcount
            
            logger.info(f"删除时间戳信息: file_id={file_id}, 删除记录数={deleted_rows}")
            
            return deleted_rows
            
        except Exception as e:
            logger.error(f"删除时间戳信息失败: {e}")
            self.connection.rollback()
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取时间戳数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {}
            
            # 总记录数
            cursor = self.connection.execute("SELECT COUNT(*) FROM video_timestamps")
            stats['total_records'] = cursor.fetchone()[0]
            
            # 按模态类型统计
            cursor = self.connection.execute("""
                SELECT modality, COUNT(*) 
                FROM video_timestamps 
                GROUP BY modality
            """)
            modality_stats = {}
            for row in cursor.fetchall():
                modality_stats[row[0]] = row[1]
            stats['by_modality'] = modality_stats
            
            # 按文件统计
            cursor = self.connection.execute("""
                SELECT COUNT(DISTINCT file_id) 
                FROM video_timestamps
            """)
            stats['unique_files'] = cursor.fetchone()[0]
            
            # 时间范围统计
            cursor = self.connection.execute("""
                SELECT MIN(start_time), MAX(end_time), AVG(duration)
                FROM video_timestamps
            """)
            time_stats = cursor.fetchone()
            if time_stats[0] is not None:
                stats['time_range'] = {
                    'min_start_time': time_stats[0],
                    'max_end_time': time_stats[1],
                    'avg_duration': time_stats[2]
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def get_precise_timestamp_by_time(self, file_id: str, target_time: float, 
                                    modality: Optional[ModalityType] = None,
                                    tolerance: float = 2.0) -> Optional[TimestampInfo]:
        """
        根据精确时间获取最匹配的时间戳信息
        
        Args:
            file_id: 文件ID
            target_time: 目标时间
            modality: 模态类型过滤
            tolerance: 时间容差
            
        Returns:
            最匹配的时间戳信息
        """
        try:
            if modality:
                query_sql = """
                SELECT *, ABS(? - (start_time + duration/2)) as time_diff
                FROM video_timestamps 
                WHERE file_id = ? AND modality = ?
                AND start_time <= ? + ? AND end_time >= ? - ?
                ORDER BY time_diff ASC
                LIMIT 1
                """
                cursor = self.connection.execute(query_sql, (
                    target_time, file_id, modality.value,
                    target_time, tolerance, target_time, tolerance
                ))
            else:
                query_sql = """
                SELECT *, ABS(? - (start_time + duration/2)) as time_diff
                FROM video_timestamps 
                WHERE file_id = ?
                AND start_time <= ? + ? AND end_time >= ? - ?
                ORDER BY time_diff ASC
                LIMIT 1
                """
                cursor = self.connection.execute(query_sql, (
                    target_time, file_id,
                    target_time, tolerance, target_time, tolerance
                ))
            
            row = cursor.fetchone()
            
            if row:
                timestamp_info = self._row_to_timestamp_info(row)
                logger.debug(f"精确时间戳查询成功: target_time={target_time}, "
                           f"found_time={timestamp_info.start_time + timestamp_info.duration/2:.3f}")
                return timestamp_info
            
            return None
            
        except Exception as e:
            logger.error(f"精确时间戳查询失败: {e}")
            return None
    
    def get_continuous_timeline(self, file_id: str, 
                              modality: Optional[ModalityType] = None,
                              min_duration: float = 1.0) -> List[TimestampInfo]:
        """
        获取连续的时间线，检测时间间隙
        
        Args:
            file_id: 文件ID
            modality: 模态类型过滤
            min_duration: 最小段时长过滤
            
        Returns:
            连续时间线的时间戳列表
        """
        try:
            if modality:
                query_sql = """
                SELECT * FROM video_timestamps 
                WHERE file_id = ? AND modality = ? AND duration >= ?
                ORDER BY start_time ASC
                """
                cursor = self.connection.execute(query_sql, (file_id, modality.value, min_duration))
            else:
                query_sql = """
                SELECT * FROM video_timestamps 
                WHERE file_id = ? AND duration >= ?
                ORDER BY start_time ASC
                """
                cursor = self.connection.execute(query_sql, (file_id, min_duration))
            
            rows = cursor.fetchall()
            
            timeline = []
            for row in rows:
                ts_info = self._row_to_timestamp_info(row)
                if ts_info:
                    timeline.append(ts_info)
            
            # 检测时间间隙
            gaps = []
            for i in range(len(timeline) - 1):
                current_end = timeline[i].end_time
                next_start = timeline[i + 1].start_time
                gap_duration = next_start - current_end
                
                if gap_duration > 0.1:  # 100ms以上的间隙
                    gaps.append({
                        'start_time': current_end,
                        'end_time': next_start,
                        'duration': gap_duration,
                        'after_segment': timeline[i].segment_id,
                        'before_segment': timeline[i + 1].segment_id
                    })
            
            if gaps:
                logger.info(f"检测到{len(gaps)}个时间间隙: file_id={file_id}")
            
            logger.debug(f"连续时间线查询完成: file_id={file_id}, 段数={len(timeline)}")
            return timeline
            
        except Exception as e:
            logger.error(f"连续时间线查询失败: {e}")
            return []
    
    def get_overlapping_segments(self, file_id: str, start_time: float, end_time: float,
                               modality: Optional[ModalityType] = None) -> List[TimestampInfo]:
        """
        获取与指定时间范围重叠的所有段
        
        Args:
            file_id: 文件ID
            start_time: 开始时间
            end_time: 结束时间
            modality: 模态类型过滤
            
        Returns:
            重叠段的时间戳列表
        """
        try:
            if modality:
                query_sql = """
                SELECT * FROM video_timestamps 
                WHERE file_id = ? AND modality = ?
                AND NOT (end_time <= ? OR start_time >= ?)
                ORDER BY start_time ASC
                """
                cursor = self.connection.execute(query_sql, (
                    file_id, modality.value, start_time, end_time
                ))
            else:
                query_sql = """
                SELECT * FROM video_timestamps 
                WHERE file_id = ?
                AND NOT (end_time <= ? OR start_time >= ?)
                ORDER BY start_time ASC
                """
                cursor = self.connection.execute(query_sql, (
                    file_id, start_time, end_time
                ))
            
            rows = cursor.fetchall()
            
            overlapping_segments = []
            for row in rows:
                ts_info = self._row_to_timestamp_info(row)
                if ts_info:
                    overlapping_segments.append(ts_info)
            
            logger.debug(f"重叠段查询完成: file_id={file_id}, "
                        f"time_range=[{start_time}, {end_time}], 段数={len(overlapping_segments)}")
            
            return overlapping_segments
            
        except Exception as e:
            logger.error(f"重叠段查询失败: {e}")
            return []
    
    def get_scene_boundaries_with_context(self, file_id: str, 
                                        context_duration: float = 5.0) -> List[Dict[str, Any]]:
        """
        获取场景边界及其上下文信息
        
        Args:
            file_id: 文件ID
            context_duration: 上下文时长
            
        Returns:
            场景边界信息列表，包含上下文
        """
        try:
            # 查询所有场景边界
            query_sql = """
            SELECT * FROM video_timestamps 
            WHERE file_id = ? AND scene_boundary = TRUE
            ORDER BY start_time ASC
            """
            cursor = self.connection.execute(query_sql, (file_id,))
            boundary_rows = cursor.fetchall()
            
            scene_boundaries = []
            
            for row in boundary_rows:
                boundary_ts = self._row_to_timestamp_info(row)
                if not boundary_ts:
                    continue
                
                boundary_time = boundary_ts.start_time
                
                # 获取前后上下文
                context_start = max(0, boundary_time - context_duration)
                context_end = boundary_time + context_duration
                
                context_segments = self.get_timestamp_infos_by_time_range(
                    file_id, context_start, context_end
                )
                
                boundary_info = {
                    'boundary_timestamp': boundary_ts,
                    'boundary_time': boundary_time,
                    'context_start': context_start,
                    'context_end': context_end,
                    'context_segments': context_segments,
                    'context_duration': context_duration * 2,
                    'segments_before': len([s for s in context_segments if s.end_time <= boundary_time]),
                    'segments_after': len([s for s in context_segments if s.start_time >= boundary_time])
                }
                
                scene_boundaries.append(boundary_info)
            
            logger.debug(f"场景边界上下文查询完成: file_id={file_id}, 边界数={len(scene_boundaries)}")
            return scene_boundaries
            
        except Exception as e:
            logger.error(f"场景边界上下文查询失败: {e}")
            return []
    
    def optimize_database(self):
        """
        优化数据库性能
        """
        try:
            # 分析表统计信息
            self.connection.execute("ANALYZE video_timestamps")
            
            # 重建索引
            self.connection.execute("REINDEX")
            
            # 清理数据库
            self.connection.execute("VACUUM")
            
            self.connection.commit()
            
            logger.info("数据库优化完成")
            
        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
    
    def _row_to_timestamp_info(self, row: sqlite3.Row) -> Optional[TimestampInfo]:
        """
        将数据库行转换为TimestampInfo对象
        
        Args:
            row: 数据库行
            
        Returns:
            TimestampInfo对象或None
        """
        try:
            # 解析模态类型
            modality_str = row['modality']
            modality = ModalityType(modality_str)
            
            # 创建TimestampInfo对象
            timestamp_info = TimestampInfo(
                file_id=row['file_id'],
                segment_id=row['segment_id'],
                modality=modality,
                start_time=row['start_time'],
                end_time=row['end_time'],
                duration=row['duration'],
                frame_index=row['frame_index'],
                vector_id=row['vector_id'],
                confidence=row['confidence'],
                scene_boundary=bool(row['scene_boundary'])
            )
            
            return timestamp_info
            
        except Exception as e:
            logger.error(f"数据库行转换失败: {e}")
            return None
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("时间戳数据库连接已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class TimestampQueryBuilder:
    """时间戳查询构建器 - 用于构建复杂的时间戳查询"""
    
    def __init__(self, db: TimestampDatabase):
        self.db = db
        self.conditions = []
        self.parameters = []
        self.order_by = "start_time ASC"
        self.limit_count = None
    
    def filter_by_file_id(self, file_id: str):
        """按文件ID过滤"""
        self.conditions.append("file_id = ?")
        self.parameters.append(file_id)
        return self
    
    def filter_by_modality(self, modality: ModalityType):
        """按模态类型过滤"""
        self.conditions.append("modality = ?")
        self.parameters.append(modality.value)
        return self
    
    def filter_by_time_range(self, start_time: float, end_time: float):
        """按时间范围过滤"""
        self.conditions.append("""
            (
                (start_time <= ? AND end_time >= ?) OR
                (start_time >= ? AND start_time <= ?) OR
                (end_time >= ? AND end_time <= ?)
            )
        """)
        self.parameters.extend([
            end_time, start_time,  # 重叠检测
            start_time, end_time,  # 开始时间在范围内
            start_time, end_time   # 结束时间在范围内
        ])
        return self
    
    def filter_by_confidence(self, min_confidence: float):
        """按置信度过滤"""
        self.conditions.append("confidence >= ?")
        self.parameters.append(min_confidence)
        return self
    
    def filter_scene_boundaries_only(self):
        """只查询场景边界"""
        self.conditions.append("scene_boundary = TRUE")
        return self
    
    def order_by_time(self, ascending: bool = True):
        """按时间排序"""
        self.order_by = "start_time ASC" if ascending else "start_time DESC"
        return self
    
    def order_by_confidence(self, ascending: bool = False):
        """按置信度排序"""
        self.order_by = "confidence ASC" if ascending else "confidence DESC"
        return self
    
    def limit(self, count: int):
        """限制结果数量"""
        self.limit_count = count
        return self
    
    def execute(self) -> List[TimestampInfo]:
        """执行查询"""
        try:
            # 构建SQL查询
            base_sql = "SELECT * FROM video_timestamps"
            
            if self.conditions:
                where_clause = " WHERE " + " AND ".join(self.conditions)
                base_sql += where_clause
            
            base_sql += f" ORDER BY {self.order_by}"
            
            if self.limit_count:
                base_sql += f" LIMIT {self.limit_count}"
            
            # 执行查询
            cursor = self.db.connection.execute(base_sql, self.parameters)
            rows = cursor.fetchall()
            
            # 转换结果
            timestamp_infos = []
            for row in rows:
                ts_info = self.db._row_to_timestamp_info(row)
                if ts_info:
                    timestamp_infos.append(ts_info)
            
            logger.debug(f"查询构建器执行完成: 返回{len(timestamp_infos)}条记录")
            
            return timestamp_infos
            
        except Exception as e:
            logger.error(f"查询构建器执行失败: {e}")
            return []