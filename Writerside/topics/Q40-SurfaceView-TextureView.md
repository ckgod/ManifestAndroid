# Q40) SurfaceView, TextureView

## TextureView 대신 SurfaceView를 사용해야 하는 경우 {#when-to-use-surfaceview}

`SurfaceView`는 전용 그리기(drawing) surface을 제공하는 특수 `View`로, 렌더링이 별도의 스레드에서 처리되는 시나리오를 위해 설계되었습니다. 
이는 성능이 중요한 **비디오 재생**, **커스텀 그래픽 렌더링** 또는 **게임**과 같은 작업에 일반적으로 사용됩니다.
`SurfaceView`의 주요 기능은 메인 `UI` 스레드 외부에서 별도의 표면을 생성하여 다른 `UI` 작업을 차단하지 않고 효율적인 렌더링을 가능하게 한다는 것입니다.

Surface는 `SurfaceHolder callback methods`를 통해 생성 및 관리되며, 필요에 따라 렌더링을 시작하고 중지할 수 있습니다.
예를 들어, 낮은 수준의 `API`를 사용하여 비디오를 재생하거나 게임 루프에서 그래픽을 지속적으로 그리려면 `SurfaceView`를 사용할 수 있습니다.

```kotlin
class CustomSurfaceView(context: Context) : SurfaceView(context), SurfaceHolder.Callback {
    init {
        holder.addCallback(this)
    }

    override fun surfaceCreated(holder: SurfaceHolder) {
        // Start rendering or drawing here
    }

    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {

    }
}
```

`SurfaceView`는 지속적인 렌더링에 효율적이지만, 크기 조정이나 회전과 같은 변환에는 제한이 있어 고성능 사용 사례에는 적합하지만 동적인 `UI` 상호 작용에는 유연성이 떨어집니다.

반면에 `TextureView`는 화면 밖에서 콘텐츠를 렌더링하는 또 다른 방법을 제공하지만, `SurfaceView`와 달리 `UI` 계층 구조에 원활하게 통합됩니다.
이는 `TextureView`가 변환되거나 애니메이션될 수 있음을 의미하며, 회전, 크기 조정 및 알파 블렌딩과 같은 기능을 허용합니다.
라이브 카메라 피드를 표시하거나 사용자 정의 변환으로 비디오를 렌더링하는 것과 같은 작업에 자주 사용됩니다.

`SurfaceView`와 달리 `TextureView`는 메인 스레드에서 작동합니다. 
이로 인해 지속적인 렌더링에는 약간 덜 효율적이지만, 다른 `UI` 구성 요소와의 더 나은 통합을 가능하게 하고 실시간 변환을 지원합니다.

```kotlin
class CustomTextureView(context: Context) : TextureView(context), TextureView.SurfaceTextureListener {
    init {
        surfaceTextureListener = this
    }

    override fun onSurfaceTextureAvailable(surface: SurfaceTexture, width: Int, height:Int) {
        // Start rendering or use the SurfaceTexture
    }

    override fun onSurfaceTextureSizeChanged(surface: SurfaceTexture, width: Int, height:Int) {
        // Handle surface size changes
    }

    override fun onSurfaceTextureDestroyed(surface: SurfaceTexture): Boolean {
        // Release resources or stop rendering
        return true
    }

    override fun onSurfaceTextureUpdated(surface: SurfaceTexture) {
        // Handle updates to the surface texture
    }
}
```

`TextureView`는 비디오 스트림을 애니메이션하거나 `UI` 내에서 콘텐츠를 동적으로 블렌딩하는 것과 같이 시각적 변환이 필요한 사용 사례에 특히 유용합니다.

### SurfaceView와 TextureView의 차이점 {#differences-surfaceview-textureview}

주요 차이점은 이러한 구성 요소가 렌더링 및 `UI` 통합을 처리하는 방식에 있습니다.
`SurfaceView`는 별도의 스레드에서 작동하므로 비디오 재생 또는 게임과 같은 지속적인 렌더링 작업에 효율적입니다.
또한 렌더링을 위한 별도의 창을 생성하여 성능을 보장하지만, 변환되거나 애니메이션되는 기능이 제한됩니다.

대조적으로, `TextureView`는 다른 `UI` 구성 요소와 동일한 창을 공유하므로 크기를 조정하거나 회전하거나 애니메이션할 수 있어 `UI` 관련 사용 사례에 더 유연합니다.
그러나 메인 스레드에서 작동하므로 고주파 렌더링이 필요한 작업에는 효율성이 떨어질 수 있습니다.

### 요약 {#summary}

`SurfaceView`는 게임 또는 지속적인 비디오 렌더링과 같이 성능이 가장 중요한 시나리오에 가장 적합합니다.
반면에 `TextureView`는 비디오 애니메이션 또는 라이브 카메라 피드 표시와 같이 원활한 `UI` 통합 및 시각적 변환이 필요한 사용 사례에 더 적합합니다.
둘 중 어떤 것을 선택할지는 애플리케이션이 성능과 `UI` 유연성 중 어느 것을 우선시하는지에 따라 달라집니다.


<deflist collapsible="true" default-state="collapsed">
<def title="Q) 효율적인 리소스 관리 및 메모리 누수 방지를 위해 `SurfaceView`의 생명주기를 올바르게 관리하는 방법은 무엇입니까?">

`SurfaceView`는 메인 UI 스레드가 아닌 별도의 백그라운드 스레드에서 화면을 그리기 때문에, 생명주기 관리가 일반 `View`보다 복잡합니다. 

올바르지 않은 관리는 앱 크래시, 배터리 과다 소모, 메모리 누수의 직접적인 원인이 됩니다. 

1. SurfaceHolder.Callback 구현

`SurfaceView`의 생명주기는 `Activity`의 생명주기와 정확히 일치하지 않습니다. 따라서 `SurfaceHolder.Callback` 인터페이스를 구현하여 Surface의 상태 변화(생성, 변경, 파괴)를 정확히 감지해야 합니다.
* **surfaceCreated()**: Surface가 생성된 직후 호출됩니다. 여기서 렌더링 스레드를 시작해야 합니다.
* **surfaceChanged()**: Surface의 포맷이나 크기가 변경될 때 호출됩니다. 화면 크기에 맞게 렌더링 로직을 업데이트 합니다.
* **surfaceDestroyed()**: Surface가 파괴되기 직전에 호출됩니다. 여기서 반드시 렌더링 스레드를 안전하게 종료시켜야 합니다.

2. 스레드 동기화 및 안전한 종료

가장 흔한 실수는 `Activity`가 종료되었는데도 백그라운드 렌더링 스레드가 계속 돌아가는 경우입니다. 이를 방지하기 위해 플래그 패턴과 `Tread.join()`을 사용해야 합니다.

```Kotlin
class MySurfaceView(context: Context) : SurfaceView(context), SurfaceHolder.Callback {

    private var renderThread: RenderThread? = null

    init {
        // Callback 등록
        holder.addCallback(this)
    }

    override fun surfaceCreated(holder: SurfaceHolder) {
        // Surface가 준비되었으므로 스레드 시작
        renderThread = RenderThread(holder)
        renderThread?.setRunning(true)
        renderThread?.start()
    }

    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {
        // 화면 크기 변경 대응 (예: 가로/세로 모드 전환)
    }

    override fun surfaceDestroyed(holder: SurfaceHolder) {
        // 스레드 종료 시그널 전송
        var retry = true
        renderThread?.setRunning(false)
        
        while (retry) {
            try {
                // 스레드가 완전히 종료될 때까지 대기 (동기화)
                renderThread?.join()
                retry = false
            } catch (e: InterruptedException) {
                e.printStackTrace()
            }
        }
    }

    // 내부 렌더링 스레드 클래스
    class RenderThread(private val surfaceHolder: SurfaceHolder) : Thread() {
        private var isRunning = false

        fun setRunning(run: Boolean) {
            isRunning = run
        }

        override fun run() {
            while (isRunning) {
                var canvas: Canvas? = null
                try {
                    // 캔버스 잠금 및 그리기 준비 (동기화 블록 권장)
                    canvas = surfaceHolder.lockCanvas()
                    synchronized(surfaceHolder) {
                        if (canvas != null) {
                            // 실제 그리기 로직 (update() -> draw())
                            // drawMyScene(canvas)
                        }
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                } finally {
                    if (canvas != null) {
                        try {
                            // 다 그렸으면 캔버스 해제 및 포스트
                            surfaceHolder.unlockCanvasAndPost(canvas)
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }
                }
            }
        }
    }
}
```

3. Activity 생명주기와의 연동 (`onPause`, `onResume`)

`SurfaceView`자체의 콜백만으로 부족할 때가 있습니다. 사용자가 홈 버튼을 눌러 앱을 백그라운드로 보냈을 때, Surface는 파괴되지 않을 수도 있지만 리소스를 아끼기 위해 렌더링을 멈춰야합니다.

* **onPause()**: 렌더링 스레드를 일지 정지 시키거나 종료하여 CPU/GPU 자원을 반환해야 합니다.
* **onResume()**: 스레드를 다시 시작하거나 재개합니다.

4. 추가 체크 사항들

* Context 참조 주의: `RenderThread` 내부에서 Activity의 Context를 강하게 참조하고 있으면, 액티비티가 종료되어도 GC가 회수하지 못합니다. 필요한 경우 `WeakReference`를 사용하거나 리소스를 분리해야합니다.
* Bitmap 리소스 해제: 렌더링에 사용하는 무거운 비트맵 리소스는 `surfaceDestroyed` 시점에 명시적으로 `recycle()` 하거나 `null` 처리를 하여 메모리를 확보하는 것이 좋습니다. 
* 예외 처리: `lockCanvas()` 는 `Surface`가 유효하지 않을 때 `null` 을 반환하거나 예외를 던질 수 있습니다. 반드시 `try-catch`와 `null check`를 해야 앱이 비정상 종료되는 것을 막을 수 있습니다.

</def>
<def title="Q) 회전 및 크기 조정과 같은 변환과 함께 라이브 카메라 미리 보기를 표시해야 하는 요구 사항이 있을 때, `SurfaceView`와 `TextureView` 중 어떤 구성 요소를 선택하시겠습니까? 구현 고려 사항과 함께 선택을 정당화하십시오.">

**TextureView를 선택하겠습니다.** 

주어진 요구사항인 실시간 카메라 미리보기와 함꼐 회전 및 스케일링과 같은 변환 적용을 고려했을 때, TextureView가 구현 용이성과 기능적 적합성 면에서 더 우수하기 때문입니다.

가장 큰 이유는 Android 뷰 계층 구조 내에서의 동작 방식 차이입니다. 

* TextureView의 강점
  * TextureView는 일반적인 View 처럼 작동합니다. 즉, `View.setTranslation()`, `View.setScale()`, `View.setRotation()` 등의 표준 API를 그대로 사용할 수 있습니다. 
  * 특히 `setTranform(Matrix matrix)` 메서드를 지원하여, 카메라 미리보기 화면에 대한 복잡한 매트릭스 연산(비틀기, 회전, 확대/축소)를 매우 쉽게 적용할 수 있습니다. 
  * 다른 뷰와 겹치거나(Overlay), 투명도(Alpha)를 조절하고, 애니메이션을 적용하는 것이 자유롭습니다. 
* SurfaceView의 한계
  * SurfaceView는 앱의 윈도우 뒤쪽에 별도의 레이어(구멍을 뚫어놓은 형태)로 존재합니다.
  * 이 때문에 뷰 계층 구조에 종속되지 않아 일반적인 View의 변환(회전, 스케일링)이 제대로 적용되지 않거나, 적용하더라도 주변 UI와 동기화가 맞지 않아 찢어지는 현상이 발생할 수 있습니다.
  * 단순히 크기를 바꾸는 것은 가능하지만, 실시간으로 부드럽게 회전하거나 애니메이션을 주는 구현은 매우 복잡하고 어렵습니다.

TextureView를 선택합에 있어 개발자가 반드시 인지해야 할 트레이드오프(Trade-off)가 있습니다. 

1. 성능 및 배터리 소모
   * SurfaceView: 그래픽 버퍼가 디스플레이 하드웨어로 직접 전송되므로 성능이 매우 뛰어나고 배터리 소모가 적습니다.
   * TextureView: 콘텐츠를 렌더링하기 위해 내부적으로 OpenGL 텍스처 인스턴스로 복사하는 과정이 필요합니다. 이로 인해 SurfaceView 대비 메모리 사용량이 높고 배터리 소모가 큽니다.
2. 메인 스레드 부하
   * TextureView의 갱신은 경우에 따라 메인 UI스레드에 부하를 줄 수 있습니다. 반면 SurfaceView는 백그라운드 스레드에서 완전히 독립적으로 그리기가 가능합니다.
3. 화면 캡처 용이성
   * TextureView.getBitmap() 메서드를 제공하므로, 현재 카메라 프리뷰 화면을 캡처하여 저장하거나 블러효과를 주어 배경으로 쓰는 등의 UI 구현이 SurfaceView보다 훨씬 간단합니다.

</def>
</deflist>