# Q38) invalidate()

## View 시스템에서 무효화(invalidation)란 무엇인가요?

무효화(Invalidation)는 View를 다시 그려야 함을 표시하는 프로세스를 말합니다.
이는 변경 사항이 발생할 때 UI를 업데이트하기 위해 Android View 시스템에서 사용되는 기본적인 메커니즘입니다.
View가 무효화되면 시스템은 다음 드로잉 주기 동안 화면의 해당 부분을 새로 고쳐야 함을 인지합니다.

### 무효화(Invalidation) 작동 방식 {#i1}

View에서 `invalidate()` 또는 `postInvalidate()`와 같은 메서드를 호출하면 무효화 프로세스가 트리거됩니다.
시스템은 해당 View를 "dirty" 상태로 플래그하여 다시 그려야 함을 나타냅니다.
다음 프레임 동안 시스템은 무효화된 View를 드로잉 패스에 포함하여 시각적 표현을 업데이트합니다.

예를 들어, View의 위치, 크기 또는 모양과 같은 속성이 변경될 때, 무효화는 사용자가 업데이트된 상태를 볼 수 있도록 합니다.

### 무효화를 위한 주요 메서드

1. `invalidate()`: 이 메서드는 단일 View를 무효화하는 데 사용됩니다. View를 dirty 상태로 표시하여 다음 레이아웃 패스 동안 시스템이 다시 그리도록 신호를 보냅니다. View를 즉시 다시 그리는 것이 아니라 다음 프레임을 위해 예약합니다.
2. `invalidate(Rect dirty)`: 이는 `invalidate()`의 오버로드된 버전으로, View 내에서 다시 그려야 하는 특정 사각형 영역을 지정할 수 있습니다. 이는 View의 더 작은 부분으로만 다시 그리기를 제한하여 성능을 최적화합니다.
3. `postInvalidate()`: 이 메서드는 비-UI 스레드에서 View를 무효화하는 데 사용됩니다. 무효화 요청을 메인 스레드에 게시하여 스레드 안전성을 보장합니다.

### `invalidate()`를 사용하여 사용자 정의 View 업데이트하기

아래는 상태가 변경될 때 UI를 다시 그리기 위해 `invalidate()` 메서드가 사용되는 사용자 정의 View의 예시입니다.

```Kotlin
class CustomView(context: Context) : View(context) {
    private var circleRadius = 50f

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        // Draw a circle with the current radius
        canvas.drawCircle(width / 2f, height / 2f, circleRadius, Paint().apply { color = Color.RED })
    }

    fun increaseRadius() {
        circleRadius += 20f
        invalidatea() // Mark the View as needing to be redrawn
    }
}
```

### 무효화(Invalidation)를 위한 모범 사례

* View의 특정 영역만 다시 그려야 할 때 부분 업데이트를 위해 `invalidate(Rect dirty)`를 사용하세요. 이는 변경되지 않은 영역을 불필요하게 다시 그리는 것을 피하여 성능을 향상시킵니다.
* 특히 애니메이션 또는 복잡한 레이아웃에서 성능 병목 현상을 방지하기 위해 `invalidate()`를 자주 또는 불필요하게 호출하는 것을 피하세요.
* 백그라운드 스레드에서 무효화 요청을 할 때는 `postInvalidate()`를 사용하여 업데이트가 메인 스레드에서 안전하게 발생하도록 하세요.

### 요약

무효화(Invalidation)는 UI 업데이트가 시각적으로 반영되도록 보장하는 Android 렌더링 파이프라인의 중요한 개념입니다.
`invalidate()` 또는 `postInvalidate()`와 같은 메서드를 사용함으로써 개발자는 원활한 성능을 유지하면서 View를 효율적으로 새로 고칠 수 있습니다.
무효화의 적절한 사용은 불필요한 다시 그리기를 최소화하여 최적화되고 반응성이 뛰어난 애플리케이션으로 이어집니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) invalidate() 메서드는 어떻게 작동하며, postInvalidate()와 어떻게 다른가요? 각각이 적절한 실제 사용 사례를 제공하세요.">
`invalidate()`와 `postInvalidate()`는 어느 스레드에서 호출하느냐가 가장 결정적인 차이입니다.

1. `invalidate()`: UI 스레드 전용
   * 뷰의 특정 영역이 변경되었음(Dirty)을 시스템에 알립니다.
   * 안드로이드 프레임워크는 다음 렌더링 사이클(V-sync)에 해당 뷰의 `onDraw()` 메서드를 호출하도록 예약합니다.
   * 즉시 그리는 것이 아니라, 메시지 큐에 다시 그려라라는 작업을 요청하는 방식입니다.
2. `postInvalidate()`: 백그라운드 스레드용
   * 내부적으로 Handler를 사용하여 UI 스레드의 메시지 큐에 `invalidate` 요청을 전달합니다.
   * UI 스레드가 해당 메시지를 처리할 때 비로소 `invalidate()`가 호출되고, 이후 과정은 동일합니다.

**실제 사용 사례**

1. `invalidate()` 사용 - 커스텀 볼륨 조절 뷰

사용자가 화면을 드래그하여 볼륨을 조절하는 커스텀 뷰

```Kotlin
class VolumeControlView(context: Context) : View(context) {
    private var volumeLevel = 0f

    override fun onTouchEvent(event: MotionEvent): Boolean {
        // 터치 위치에 따라 볼륨 레벨 계산
        volumeLevel = calculateVolume(event.y)
        
        // UI 스레드에서 발생한 이벤트이므로 즉시 다시 그리기 요청
        // onDraw()가 호출되어 변경된 볼륨 바를 그림
        invalidate() 
        return true
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        // volumeLevel에 따라 사각형(Bar) 그리기
    }
}
```

2. `postInvalidate()` 사용 - 실시간 오디오 파형

음악 재생 중 오디오 데이터를 분석하여 파형을 그려주는 뷰

```Kotlin
class AudioVisualizerView(context: Context) : View(context) {
    private var waveformData: ByteArray? = null

    // 백그라운드 스레드에서 실행되는 분석 로직
    fun startVisualizing() {
        Thread {
            while (isPlaying) {
                // 1. 복잡한 오디오 데이터 분석 (CPU 작업)
                val newData = analyzeAudioStream()
                
                // 2. 데이터 업데이트
                this.waveformData = newData

                // 3. 백그라운드 스레드이므로 postInvalidate() 호출
                // 메인 스레드에게 "다시 그려달라"고 메시지를 보냄
                postInvalidate() 
                
                Thread.sleep(16) // 약 60fps 유지
            }
        }.start()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        // waveformData를 이용해 파형 그리기
    }
}
```

**최신 안드로이드 개발에서의 고려사항**

최근 안드로이드 개발 트렌드(Coroutines, RxJava, Jetpack Compose)에서는 `postInvalidate()`를 직접 호출하는 빈도가 줄어들고 있습니다. 

* **Coroutine 사용 시**: `withContext(Dispatchers.Main)`을 사용하여 UI스레드로 전환한 뒤 `invalidate()`를 호출하거나, LiveData/StateFlow를 관찰(Observe)하여 뷰를 갱신하는 패턴이 더 일반적입니다.
* **Jetpack Compose**: `invalidate()` 개념이 사라지고, State(상태)가 변경되면 컴포저블 함수가 자동으로 Recomposition 됩니다.

</def>
<def title="Q) 백그라운드 스레드에서 UI 요소를 업데이트해야 하는 경우, 다시 그리기 작업이 메인 스레드에서 안전하게 수행되도록 어떻게 보장하시겠습니까?">

백그라운드 스레드에서 UI를 업데이트하려고 할 떄, 안드로이드의 단일 스레드 모델 정책을 준수하면서 안전하게 메인 스레드로 제어권을 넘기는 방법은 여러 가지가 있습니다.

**1. Kotlin Coroutines**

현대적인 안드로이드 개발, 특히 MVVM 패턴에서는 코루틴을 사용하는 것이 표준입니다. 스레드 컨텍스트 전환이 매우 간결하며 가독성이 높습니다.
* `withContext(Dispatchers.Main)`: 백그라운드 작업 도중 UI 갱신이 필요할 때 잠시 메인 스레드로 전환합니다.
* `lifecycleScope` / `viewLifecycleOwner.lifecycleScope`: 액티비티나 프래그먼트의 수명 주기에 맞춰 안전하게 코루틴을 실행합니다.

**2. Reactive Streams (LiveData / StateFlow)**

UI 컨트롤러가 데이터를 관찰하게 만드는 방식입니다. 이 방식은 스레드 안정성을 데이터 홀더가 보장해주거나, 관찰 자체가 메인 스레드에서 이루어지도록 설계되어 있습니다.

* LiveData: `postValue()` 메서드를 사용하면 백그라운드 스레드에서 안전하게 값을 세팅할 수 있으며, 관찰자(UI)는 메인 스레드에서 변경 사항을 수신합니다.
* StateFlow: `update`를 통해 상태를 변경하고, UI에서는 `collect`를 통해 데이터를 받습니다.

**3. `View.post()` 및 `View.postDelayed()`**

특정 뷰에 종속적인 작업이거나, 뷰가 화면에 부착(Attached)된 이후에 실행되어야 할 때 유용합니다.
내부적으로 핸들러를 사용합니다.

</def>
</deflist>