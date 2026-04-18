# Q53) LiveData

## LiveData는 무엇인가요? {#what-is-livedata}

`LiveData`는 Android Jetpack Architecture Components에서 제공하는 관찰 가능한(observable) 데이터 홀더 클래스입니다. 가장 큰 특징은 **수명 주기를 인식한다(lifecycle-aware)** 는 점으로, 자신을 관찰하는 Activity나 Fragment의 수명 주기를 인지하여 해당 컴포넌트가 활성 상태(`STARTED` 또는 `RESUMED`)일 때만 UI 업데이트를 전달합니다.

LiveData의 핵심 목적은 UI 컴포넌트가 데이터 변경을 관찰(observe)하고, 데이터가 바뀔 때마다 UI를 자동으로 갱신하도록 하는 것입니다. 이러한 특성 덕분에 LiveData는 Android 앱에서 반응형(reactive) UI 패턴을 구현하는 핵심 도구로 사용됩니다.

### LiveData의 주요 장점 {#advantages}

LiveData가 제공하는 이점은 다음과 같습니다.

1.  **수명 주기 인식(Lifecycle Awareness)**: 컴포넌트가 활성 상태일 때만 데이터를 업데이트하므로, 비활성 상태인 화면에 대한 불필요한 갱신을 막아 크래시와 메모리 누수의 위험을 줄여 줍니다.
2.  **자동 정리(Automatic Cleanup)**: 컴포넌트의 수명 주기가 종료되면 해당 컴포넌트에 연결된 옵저버가 자동으로 제거되어, 별도의 해제 코드를 작성할 필요가 없습니다.
3.  **옵저버 패턴(Observer Pattern)**: LiveData가 보유한 데이터가 변경되면, 등록된 옵저버를 통해 UI 컴포넌트가 자동으로 갱신됩니다.
4.  **스레드 안전성(Thread Safety)**: 백그라운드 스레드에서는 `postValue()`로, 메인 스레드에서는 `setValue()`로 안전하게 데이터를 업데이트할 수 있습니다. 자세한 내용은 [setValue()와 postValue()의 차이](Details-setValue-vs-postValue.md)에서 다룹니다.

### LiveData 사용 예시 {#usage-example}

다음은 ViewModel에서 LiveData를 사용해 UI 관련 데이터를 관리하는 일반적인 패턴입니다.

```kotlin
// ViewModel
class MyViewModel : ViewModel() {
    private val _data = MutableLiveData<String>() // 내부 수정용 MutableLiveData
    val data: LiveData<String> get() = _data       // 외부에는 읽기 전용 LiveData로 노출

    fun updateData(newValue: String) {
        _data.value = newValue // LiveData 값을 갱신
    }
}

// Fragment 또는 Activity
class MyFragment : Fragment() {
    private val viewModel: MyViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // LiveData 관찰
        viewModel.data.observe(viewLifecycleOwner) { updatedData ->
            // 새 데이터로 UI 갱신
            textView.text = updatedData
        }
    }
}
```
{title="LiveData Example.kt"}

위 예시에서 `MyViewModel`이 데이터를 보유하고, `MyFragment`가 해당 LiveData를 관찰합니다. `updateData()`가 호출되면 등록된 옵저버를 통해 UI가 자동으로 갱신됩니다.

### MutableLiveData와 LiveData의 차이 {#mutablelivedata-vs-livedata}

-   **MutableLiveData**: `setValue()`와 `postValue()`를 통해 데이터를 변경할 수 있는 가변 버전입니다. 일반적으로 ViewModel 내부에 `private`으로 두어 외부의 직접 수정 가능성을 차단합니다.
-   **LiveData**: 외부 컴포넌트가 데이터를 임의로 변경하지 못하도록 막는 읽기 전용 버전입니다. ViewModel은 외부에 LiveData 타입으로만 노출하여 캡슐화를 강화합니다.

이 패턴(내부 `MutableLiveData` + 외부 `LiveData`)은 단방향 데이터 흐름을 보장하는 표준 관용구로 자리 잡았습니다.

### LiveData의 사용 사례 {#use-cases}

LiveData는 다음과 같은 시나리오에서 가장 자주 사용됩니다.

1.  **UI 상태 관리**: 네트워크 응답이나 데이터베이스 결과 같은 데이터의 컨테이너로 사용되어 UI 컴포넌트와 자연스럽게 결합됩니다. 데이터가 바뀔 때마다 UI가 자동으로 동기화되므로 화면 상태가 항상 앱 상태와 일치합니다.
2.  **옵저버 패턴 구현**: LiveData는 발행자(publisher), 옵저버는 구독자(subscriber) 역할을 하는 옵저버 패턴을 구현합니다. 값이 바뀌면 구독자에게 실시간으로 변경이 전달되므로 데이터 기반 UI 갱신에 매우 적합합니다.
3.  **일회성 이벤트(One-time Events)**: 토스트 표시나 화면 이동처럼 한 번만 처리해야 하는 이벤트에도 사용할 수 있지만, 최신 권장 방식은 `SharedFlow`나 `Channel` 등 Flow 기반 API입니다. 자세한 비교는 "Q) 66. Where do you launch tasks for loading the initial data?" 항목을 참고하세요.

### LiveData vs Flow {#livedata-vs-flow}

LiveData는 Kotlin의 `StateFlow`, `SharedFlow`와 자주 비교되며, 일부에서는 "StateFlow가 등장한 이후 LiveData는 사실상 구식"이라고 주장합니다. 하지만 이는 명확한 오해입니다. Flow는 플랫폼에 종속되지 않는(platform-agnostic) API로, **Android의 수명 주기를 알지 못합니다**. 따라서 Flow를 안전하게 사용하려면 수명 주기에 맞춰 명시적으로 수집(collect)을 시작·취소해야 합니다.

수명 주기를 고려하지 않고 Flow를 수집하면, UI가 비활성 상태일 때도 수집이 계속되어 메모리 누수 위험이 커집니다. 반면 LiveData는 `LifecycleOwner`에 바인딩되어 자동으로 구독을 해제하므로, 상황에 따라서는 더 안전하고 실용적인 선택지가 됩니다.

또한 "LiveData를 Flow로 마이그레이션하면 Android 의존성을 제거할 수 있다"는 주장도 큰 설득력을 갖기 어렵습니다. 실제로 LiveData는 보통 ViewModel 경계 안에서만 쓰이며, Jetpack 라이브러리를 모두 걷어내고 JVM-only 아키텍처로 옮기는 것이 성능이나 구조 측면에서 명확한 이득을 준다고 단정하기는 어렵습니다.

유행을 따르기보다는 고급 데이터 변환이나 복합적인 reactive stream이 필요한 시점에서 Flow를 도입하는 것이 좋습니다. Android UI에서 Flow를 안전하게 수집하는 방법은 Manuel Vivo의 *A safer way to collect flows from Android UIs* 글을 참고하세요.

### 요약 {#summary}

<tldr>

LiveData는 수명 주기를 인식하는 관찰 가능한 데이터 홀더로, MVVM 아키텍처에서 반응형이고 안전한 UI 상태 관리를 단순화합니다. 데이터 변경을 수명 주기에 맞춰 관찰하므로 보일러플레이트와 메모리 누수 가능성을 줄여 주며, 현대 Android 개발의 핵심 구성 요소로 자리 잡고 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) LiveData는 어떻게 수명 주기 인식을 보장하며, RxJava나 EventBus 같은 전통적인 옵저버블에 비해 어떤 장점을 제공하나요?">

LiveData는 옵저버를 등록할 때 `LifecycleOwner`(보통 Activity나 Fragment의 `viewLifecycleOwner`)를 함께 받습니다. 이를 통해 LiveData는 해당 컴포넌트의 수명 주기 상태를 추적하며, `STARTED` 또는 `RESUMED` 상태일 때만 옵저버에게 값을 전달합니다. 컴포넌트가 `DESTROYED` 상태가 되면 옵저버는 자동으로 제거되므로, 개발자가 별도로 해제 코드를 작성할 필요가 없습니다.

이는 RxJava나 EventBus 같은 전통적인 옵저버블과 비교했을 때 큰 장점입니다. RxJava는 `Disposable`을 직접 관리하지 않으면 Activity가 종료된 뒤에도 구독이 유지되어 메모리 누수와 크래시로 이어지기 쉽습니다. EventBus 역시 `register`/`unregister`를 수동으로 호출해야 하며, 누락하면 동일한 문제가 발생합니다. LiveData는 이러한 위험을 프레임워크 차원에서 제거해 주며, 추가 의존성 없이 Jetpack 생태계와 자연스럽게 결합된다는 점도 장점입니다.

</def>
<def title="Q) LiveData에서 setValue()와 postValue()는 어떤 차이가 있으며, 각각 언제 사용해야 하나요?">

`setValue()`는 **메인 스레드에서만** 호출할 수 있는 동기 메서드로, 호출 즉시 값이 갱신되고 같은 프레임 안에서 옵저버가 트리거됩니다. UI 이벤트 핸들러나 메인 스레드에서 직접 데이터를 갱신할 때 적합합니다. 백그라운드 스레드에서 호출하면 예외가 발생합니다.

반면 `postValue()`는 **어느 스레드에서든** 호출 가능한 비동기 메서드입니다. 내부적으로 `ArchTaskExecutor`를 통해 메인 스레드 큐에 갱신 작업을 예약하므로, 스레드 안전성을 보장하면서 백그라운드 작업의 결과를 LiveData에 반영할 수 있습니다. 네트워크 응답이나 데이터베이스 쿼리 결과를 LiveData로 노출할 때 흔히 사용됩니다.

한 가지 주의할 점은, 메인 스레드에서 `postValue("a")`를 호출한 직후 `setValue("b")`를 호출하면, `setValue("b")`가 먼저 동기적으로 적용된 뒤 곧이어 처리되는 `postValue("a")`가 다시 값을 덮어씁니다. 또한 짧은 시간 안에 `postValue()`를 여러 번 호출하면 마지막 값만 디스패치된다는 점도 기억해야 합니다. 더 자세한 비교는 [setValue()와 postValue()의 차이](Details-setValue-vs-postValue.md)에서 다룹니다.

</def>
<def title="Q) LiveData의 한계는 무엇이며, 화면 회전 같은 구성 변경 시 일회성 UI 이벤트(내비게이션, 토스트 메시지 등)가 다시 트리거되지 않도록 하려면 어떻게 처리해야 하나요?">

LiveData의 가장 큰 한계는 **상태(state)는 잘 표현하지만 이벤트(event) 표현에는 부적합하다**는 점입니다. LiveData는 마지막 값을 보유한 채 새 옵저버가 붙을 때 즉시 그 값을 전달합니다. 화면 회전 등으로 Activity/Fragment가 재생성되어 옵저버가 다시 구독을 시작하면, 이전에 이미 처리한 "토스트를 띄워라" 같은 이벤트 값이 한 번 더 전달되어 중복 실행되는 문제가 발생합니다.

전통적인 회피책은 `SingleLiveEvent`나 `Event<T>` 래퍼 패턴을 도입해 이벤트가 한 번 소비되면 다시 전달되지 않도록 처리하는 것이었습니다. 하지만 두 방식 모두 다중 옵저버 시나리오에서 한계가 있고, 결국 임시방편에 가깝습니다.

현대적으로 권장되는 접근은 일회성 이벤트는 `Channel` 또는 `SharedFlow`(replay = 0)로 모델링하고, UI에서는 `repeatOnLifecycle(STARTED)`와 함께 수집하는 방식입니다. 이렇게 하면 이벤트가 큐에서 한 번만 소비되며, 구성 변경으로 옵저버가 다시 붙어도 과거 이벤트가 재방송되지 않습니다. 즉 **상태는 LiveData/StateFlow로, 이벤트는 SharedFlow/Channel로** 역할을 분리하는 것이 표준 패턴입니다.

</def>
</deflist>
