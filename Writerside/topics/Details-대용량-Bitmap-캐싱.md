# Details: 대용량 Bitmap 캐싱

## 커스텀 이미지 로딩 시스템에서 대용량 Bitmap을 어떻게 캐싱하시겠습니까? {#bitmap-caching}

이미지 목록이나 그리드처럼 반복적으로 이미지를 표시하는 화면에서는 캐싱이 필수입니다. Android는 두 가지 전략을 제공합니다. `LruCache`를 활용한 메모리 캐싱과 `DiskLruCache`를 활용한 디스크 캐싱입니다. 두 방법을 조합하면 성능과 영속성을 모두 확보할 수 있습니다.

### LruCache를 활용한 메모리 캐싱 {#lru-cache}

`LruCache`는 최근 사용된 항목에 대한 강한 참조를 유지하며, 메모리가 부족해지면 가장 오래된 항목부터 자동으로 제거합니다.

```kotlin
object LruCacheManager {
    val maxMemory = (Runtime.getRuntime().maxMemory() / 1024).toInt()
    val cacheSize = maxMemory / 8

    val memoryCache = object : LruCache<String, Bitmap>(cacheSize) {
        override fun sizeOf(key: String, bitmap: Bitmap): Int {
            return bitmap.byteCount / 1024
        }
    }
}
```
{title="MemoryCacheInit.kt"}

사용 가능한 메모리의 1/8 정도를 캐시 용량으로 할당하는 것이 안전합니다. `SoftReference`나 `WeakReference`는 가비지 컬렉션에 의해 신뢰성이 떨어지므로 캐싱 목적으로는 사용하지 않는 것이 좋습니다.

캐시를 활용하는 방법은 다음과 같습니다. 메모리에 캐시가 있으면 바로 사용하고, 없으면 `WorkManager`를 통해 백그라운드에서 디코딩하고 캐시에 저장합니다.

```kotlin
fun loadBitmap(imageId: Int, imageView: ImageView) {
    val key = imageId.toString()
    LruCacheManager.memoryCache.get(key)?.let {
        imageView.setImageBitmap(it)
    } ?: run {
        imageView.setImageResource(R.drawable.image_placeholder)

        val workRequest = OneTimeWorkRequestBuilder<BitmapDecodeWorker>()
            .setInputData(workDataOf("imageId" to imageId))
            .build()
        WorkManager.getInstance(context).enqueue(workRequest)
    }
}
```
{title="MemoryCacheUsage.kt"}

### DiskLruCache를 활용한 디스크 캐싱 {#disk-lru-cache}

메모리는 용량이 제한적이고 앱이 종료되면 사라집니다. `DiskLruCache`를 사용하면 Bitmap을 디스크에 저장하여 앱 세션이 재시작되어도 이미지를 재사용할 수 있습니다. 특히 스크롤 가능한 이미지 목록에서 유용합니다.

```kotlin
class DiskCacheManager(val context: Context) {

    private val cachePath = context.cacheDir.path
    private val cacheFile = File(cachePath + File.separator + "images")
    private val diskLruCache = DiskLruCache.open(cacheFile, 1, 1, 10 * 1024 * 1024)

    fun filenameForKey(key: String): String {
        return MessageDigest
            .getInstance("SHA-1")
            .digest(key.toByteArray())
            .joinToString(separator = "", transform = { Integer.toHexString(0xFF and it.toInt()) })
    }

    fun get(key: String): Bitmap? {
        return try {
            val filename = filenameForKey(key)
            val inputStream = diskLruCache.get(filename).getInputStream(0)
            BitmapFactory.decodeStream(inputStream)
        } catch (e: Exception) {
            null
        }
    }

    fun set(key: String, bitmap: Bitmap) {
        val filename = filenameForKey(key)
        val snapshot = diskLruCache.get(filename)
        if (snapshot == null) {
            val editor = diskLruCache.edit(filename)
            val outputStream = editor.newOutputStream(0)
            bitmap.compress(Bitmap.CompressFormat.JPEG, 100, outputStream)
            editor.commit()
            outputStream.close()
        } else {
            snapshot.getInputStream(0).close()
        }
    }
}
```
{title="DiskCacheManager.kt"}

이 클래스는 SHA-1 기반 파일명 생성, 안전한 I/O 처리, 중복 쓰기 방지를 보장합니다.

### 메모리 + 디스크 하이브리드 전략 {#hybrid-caching-strategy}

`WorkManager`의 `CoroutineWorker`를 활용하면 메모리 캐시와 디스크 캐시를 함께 사용하는 하이브리드 전략을 안전하게 구현할 수 있습니다. 디스크에서 먼저 확인하고, 없을 경우 디코딩 후 두 캐시에 모두 저장합니다.

```kotlin
class BitmapWorker(
    private val context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        val key = inputData.getString("imageKey") ?: return Result.failure()
        val resId = inputData.getInt("resId", -1)
        if (resId == -1) return Result.failure()

        // 디스크 캐시에서 먼저 확인
        val bitmapFromDisk = diskCacheManager.get(key)
        if (bitmapFromDisk != null) {
            LruCacheManager.memoryCache.put(key, bitmapFromDisk)
            return Result.success()
        }

        // 디스크에 없으면 디코딩 후 양쪽 캐시에 저장
        val bitmap = decodeSampledBitmapFromResource(
            applicationContext.resources,
            resId,
            reqWidth = 100,
            reqHeight = 100
        )

        return try {
            if (LruCacheManager.memoryCache.get(key) == null) {
                LruCacheManager.memoryCache.put(key, bitmap)
            }
            diskCacheManager.set(key, bitmap)
            Result.success()
        } catch (e: Exception) {
            Result.failure()
        }
    }
}

private fun addBitmapToCache(diskCacheManager: DiskCacheManager, key: String, bitmap: Bitmap) {
    if (LruCacheManager.memoryCache.get(key) == null) {
        LruCacheManager.memoryCache.put(key, bitmap)
    }
    
    if (diskCacheManager.get(key) != null) {
        diskCacheManager.set(key, bitmap)
    }
}
```
{title="BitmapWorker.kt"}

`DiskCacheManager` 인스턴스는 Application 클래스나 의존성 주입을 통해 관리해야 합니다. Worker가 실행될 때마다 새로 생성하면 디스크 캐싱의 의미가 없어집니다.

### 요약 {#summary}

대용량 Bitmap을 효율적으로 캐싱하려면 `LruCache`로 빠른 메모리 접근을, `DiskLruCache`로 세션 간 영속성을 확보합니다. 두 전략을 `WorkManager`와 결합한 하이브리드 방식을 사용하면 메인 스레드를 차단하지 않으면서도 이미지 로딩 성능과 사용자 경험을 크게 향상시킬 수 있습니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) LruCache와 DiskLruCache를 함께 사용할 때 인스턴스 관리는 어떻게 해야 하나요?">

`DiskCacheManager`나 `LruCache` 인스턴스를 `WorkManager`의 Worker 내부에서 직접 생성하면, Worker가 실행될 때마다 새로운 인스턴스가 만들어져 캐시가 공유되지 않습니다. 이를 방지하려면 다음 방법 중 하나를 사용해야 합니다.

1. **Application 클래스에서 싱글톤으로 관리**: `Application.onCreate()`에서 캐시 인스턴스를 초기화하고 전역으로 접근합니다.
2. **의존성 주입(Hilt/Dagger)**: 캐시 인스턴스를 싱글톤 스코프로 주입하여 앱 전반에서 동일한 인스턴스를 사용합니다.

Worker 내에서 직접 인스턴스를 생성하는 방식은 캐시 히트율을 0으로 만들어 디스크 캐시를 사용하는 이유를 완전히 무효화합니다.

</def>
</deflist>
