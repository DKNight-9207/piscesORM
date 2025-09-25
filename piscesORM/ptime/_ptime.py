from datetime import datetime, timedelta, timezone
from time import time

class PiscesTime(datetime):

    @property
    def ts(self):
        return super().timestamp()
    
    @classmethod
    def from_database(cls, time_str, time_shift:int|timezone=0) -> "PiscesTime":
        """
        time str: ISO 8601 string.
        time_shift: if the string have no timezone information, use this as its time zone.
        """
        if isinstance(time_shift, int):
            time_shift = timezone(timedelta(hours=time_shift))

        dt_obj = datetime.fromisoformat(time_str)

        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=time_shift)
        
        return cls.fromtimestamp(dt_obj.timestamp(), tz=dt_obj.tzinfo)
    
    @classmethod
    def from_datetime(cls, datetime_obj:datetime):
        return cls(
            datetime_obj.year,
            datetime_obj.month,
            datetime_obj.day,
            datetime_obj.hour,
            datetime_obj.minute,
            datetime_obj.second,
            datetime_obj.microsecond,
            datetime_obj.tzinfo
        )
    
    def to_database(self, date_only=False, time_shift:int|timezone=0) -> str:
        if isinstance(time_shift, int):
            time_shift = timezone(timedelta(hours=time_shift))

        if getattr(self, 'tzinfo', None) is None: # 不存在時，視為從 now() 取出，時區會是本地時區
            dt_with_local_tz = self.replace(tzinfo=datetime.now().astimezone().tzinfo)
        else:
            dt_with_local_tz = self

        dt_with_tz = dt_with_local_tz.astimezone(time_shift)

        if date_only:
            return dt_with_tz.strftime('%Y-%m-%d')
        else:
            return dt_with_tz.isoformat()
        
    def __repr__(self):
        return f"<Pisces Object: {self.to_database()}>"
    
    def __str__(self):
        return self.isoformat()
    
    def __add__(self, value):
        if isinstance(value, (int, float)):
            return PiscesTime.fromtimestamp(self.ts + value)
        return super().__add__(value)
    
    def __sub__(self, value):
        if isinstance(value, (int, float)):
            return PiscesTime.fromtimestamp(self.ts - value)
        return super().__sub__(value)
    
    def __eq__(self, value):
        if isinstance(value, (int, float)):
            return PiscesTime.ts == value
        return super().__eq__(value)
    
    def __ne__(self, value):
        if isinstance(value, (int, float)):
            return PiscesTime.ts != value
        return super().__ne__(value)
    
    def __ge__(self, value):
        if isinstance(value, (int, float)):
            return PiscesTime.ts >= value
        return super().__ge__(value)
    
    def __gt__(self, value):
        if isinstance(value, (int, float)):
            return PiscesTime.ts > value
        return super().__gt__(value)
    
    def __le__(self, value):
        if isinstance(value, (int, float)):
            return PiscesTime.ts <= value
        return super().__le__(value)
    
    def __lt__(self, value):
        if isinstance(value, (int, float)):
            return PiscesTime.ts < value
        return super().__lt__(value)
    

if __name__ == "__main__":
    # time testing.

    now = PiscesTime.now()
    print(f"now: {now}")
    now_str = now.to_database()
    print(f"now_str: {now_str}")
    str_decode = PiscesTime.from_database(now_str, time_shift=timezone(timedelta(hours=8)))
    print(f"str_decode: {str_decode}")
    redecode = str_decode.to_database()
    print(f"redecode: {redecode}")