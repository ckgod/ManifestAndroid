# Q45) Bitmap

## Android에서 Bitmap이란 무엇이며, 대용량 Bitmap을 어떻게 효율적으로 처리하나요? {#what-is-bitmap}

Bitmap은 메모리 내에서 이미지를 표현하는 객체로, 픽셀 데이터를 저장하고 화면에 이미지를 렌더링하는 데 사용됩니다. 리소스, 파일, 원격 서버 등 다양한 소스에서 가져온 이미지를 UI 컴포넌트에 표시할 때 활용되며, 고해상도 이미지의 경우 메모리를 많이 차지하기 때문에 잘못 다루면 `OutOfMemoryError`로 앱이 종료될 수 있습니다.

### 대용량 Bitmap의 문제점 {#large-bitmap-problem}

카메라로 촬영한 사진이나 인터넷에서 다운로드한 이미지는 실제 UI 컴포넌트가 필요로 하는 것보다 훨씬 큰 경우가 많습니다. 이러한 이미지를 원본 해상도 그대로 로드하면 다음과 같은 문제가 발생합니다.

- 과도한 메모리 소비
- 성능 저하
- 메모리 부족으로 인한 앱 크래시

### 메모리 할당 없이 Bitmap 크기 파악하기 {#read-bitmap-dimensions}

Bitmap을 로드하기 전에 먼저 크기를 확인하는 것이 중요합니다. `BitmapFactory.Options`의 `inJustDecodeBounds = true` 옵션을 사용하면 픽셀 데이터를 메모리에 할당하지 않고 이미지 메타데이터만 읽을 수 있습니다.

```kotlin
val options = BitmapFactory.Options().apply {
    inJustDecodeBounds = true
}
BitmapFactory.decodeResource(resources, R.id.myimage, options)

val imageWidth = options.outWidth
val imageHeight = options.outHeight
val imageType = options.outMimeType
```
{title="ReadBitmapDimensions.kt"}

이 단계를 통해 이미지 크기가 화면 요구사항에 적합한지 사전에 판단할 수 있습니다.

### inSampleSize로 축소된 Bitmap 로드하기 {#load-scaled-bitmap}

이미지 크기를 파악한 후, `inSampleSize` 옵션을 사용해 Bitmap을 축소 로드할 수 있습니다. 이 값은 이미지를 2, 4, 8배 등으로 다운샘플링하여 메모리 사용량을 줄여줍니다. 예를 들어, 2048×1536 이미지를 `inSampleSize = 4`로 로드하면 512×384 크기의 Bitmap이 됩니다.

```kotlin
fun calculateInSampleSize(options: BitmapFactory.Options, reqWidth: Int, reqHeight: Int): Int {
    val (height, width) = options.run { outHeight to outWidth }
    var inSampleSize = 1

    if (height > reqHeight || width > reqWidth) {
        val halfHeight = height / 2
        val halfWidth = width / 2
        while (halfHeight / inSampleSize >= reqHeight && halfWidth / inSampleSize >= reqWidth) {
            inSampleSize *= 2
        }
    }
    return inSampleSize
}
```
{title="CalculateInSampleSize.kt"}

### 서브샘플링을 활용한 전체 디코딩 프로세스 {#full-decoding-with-subsampling}

`calculateInSampleSize`를 활용하여 두 단계로 Bitmap을 디코딩합니다.

1. 먼저 `inJustDecodeBounds = true`로 크기만 읽습니다.
2. 계산된 `inSampleSize`를 적용하고 축소된 Bitmap을 디코딩합니다.

```kotlin
fun decodeSampledBitmapFromResource(
    res: Resources,
    resId: Int,
    reqWidth: Int,
    reqHeight: Int
): Bitmap {
    return BitmapFactory.Options().run {
        inJustDecodeBounds = true
        BitmapFactory.decodeResource(res, resId, this)

        inSampleSize = calculateInSampleSize(this, reqWidth, reqHeight)
        inJustDecodeBounds = false

        BitmapFactory.decodeResource(res, resId, this)
    }
}
```
{title="DecodeSampledBitmap.kt"}

`ImageView`에 적용할 때는 다음과 같이 사용합니다.

```kotlin
imageView.setImageBitmap(
    decodeSampledBitmapFromResource(resources, R.id.myimage, 100, 100)
)
```
{title="SetImageBitmap.kt"}

### 요약 {#summary}

<tldr>
Bitmap은 Android에서 메모리를 많이 차지하는 이미지 표현 방식입니다. 대용량 Bitmap을 효율적으로 처리하려면 `inJustDecodeBounds`로 이미지 크기를 먼저 확인하고, `inSampleSize`로 다운샘플링하여 필요한 크기만 로드합니다. 이 두 단계 전략으로 메모리 부족으로 인한 앱 크래시를 예방할 수 있습니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 대용량 Bitmap을 메모리에 로드할 때 발생하는 위험은 무엇이며, 어떻게 방지할 수 있나요?">

대용량 Bitmap을 그대로 메모리에 로드하면 `OutOfMemoryError`가 발생할 수 있습니다. 이를 방지하기 위해 다음 전략을 사용합니다.

1. **크기 사전 확인**: `BitmapFactory.Options`의 `inJustDecodeBounds = true`를 사용해 메모리 할당 없이 이미지 메타데이터만 읽습니다.
2. **다운샘플링**: `inSampleSize` 값을 계산하여 필요한 크기에 맞게 이미지를 축소 로드합니다.
3. **메모리 캐싱**: `LruCache`를 활용해 자주 사용하는 Bitmap을 메모리에 캐싱하고 중복 디코딩을 방지합니다.
4. **디스크 캐싱**: `DiskLruCache`로 Bitmap을 영구 저장하여 앱 재시작 시에도 재사용합니다.
5. **백그라운드 처리**: `WorkManager`나 코루틴을 사용해 디코딩 작업을 메인 스레드 외부에서 수행합니다.

</def>
</deflist>
