# Q54) Jetpack ViewModel

## Jetpack ViewModel이란 무엇인가요?
Jetpack ViewModel은 UI 관련 데이터를 수명 주기를 고려하여 저장하고 관리하도록 설계된 Android Architecture Components의 핵심 구성 요소입니다. 
이는 개발자가 UI 로직과 비즈니스 로직을 분리하여 견고하고 유지보수 가능한 앱을 만들 수 있도록 돕고, 화면 회전과 같은 구성 변경 시에도 데이터가 유지되도록 보장합니다.

ViewModel의 주요 목표는 구성 변경 중 UI 관련 데이터를 보존하는 것입니다. 
예를 들어, 사용자가 기기를 회전할 때 Activity 또는 Fragment는 소멸되고 다시 생성되지만, ViewModel은 데이터가 손상되지 않고 유지되도록 보장합니다.

```Kotlin
data class DiceUiState(
    val firstDieValue: Int? = null,
    val secondDieValue: Int? = null,
    val numberOfRolls: Int = 0,
)

class DiceRollViewModel : ViewModel() {
    
    // Expose screen UI state
    private val _uiState = MutableStateFlow(DiceUiState())
    val uiState: StateFlow<DiceUiState> = _uiState.asStateFlow()
    
    // Handle business logic
    fun rollDice() {
        _uiState.update { currentState ->
            currentState.copy(
                firstDieValue = Random.nextInt(from = 1, until = 7),
                secondDieValue = Random.nextInt(from = 1, until = 7),
                numberOfRolls = currentState.numberOfRolls + 1
            )
        }
    }
}
```

이 예시에서, 구성 변경으로 인해 Activity가 다시 생성되더라도 상태 값은 유지됩니다.

### ViewModel의 특징 {#VMF1f3}
1.  **수명 주기 인식 (Lifecycle Awareness)**: ViewModel은 Activity 또는 Fragment의 수명 주기에 맞춰 범위가 지정됩니다. 사용자가 화면에서 벗어나는 등 연관된 UI 구성 요소가 더 이상 사용되지 않을 때 자동으로 소멸됩니다.
2.  **구성 변경 시 지속성 (Persistence Across Configuration Changes)**: 구성 변경 중에 소멸되고 다시 생성되는 Activity 또는 Fragment와 달리, ViewModel은 상태를 유지하여 데이터 손실을 방지하고 반복적인 데이터 재요청을 피합니다.
3.  **관심사 분리 (Separation of Concerns)**: ViewModel은 UI 관련 로직과 비즈니스 로직을 분리하여 코드를 더 깨끗하고 유지보수 가능하게 만듭니다. UI 레이어는 ViewModel을 관찰하여 업데이트를 받으므로 반응형 프로그래밍 원칙을 구현하기가 더 쉽습니다.

### ViewModel 생성 및 사용
[Jetpack activity-ktx library](https://developer.android.com/jetpack/androidx/releases/activity)에서 제공하는 Kotlin의 `by viewModels()` 델리게이트를 사용하여 `ComponentActivity`에서 ViewModel을 손쉽게 생성할 수 있습니다. 이 확장 기능은 ViewModel 생성을 단순화하여 더 깔끔하고 읽기 쉬운 코드를 보장합니다.

```Kotlin
class DiceRollActivity : AppCompatActivity() {

    // Use the 'by viewModels()' Kotlin property delegate
    // from the activity-ktx artifact
    private val viewModel: DiceRollViewModel by viewModels()
    
    override fun onCreate(savedInstanceState: Bundle?) {
        // Create a ViewModel the first time the system calls an activity's onCreate() method.
        // Re-created activities receive the same DiceRollViewModel instance created by the first activity.
        
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect {
                    // Update UI elements
                }
            }
        }
    }
}
```

ViewModel 인스턴스는 ViewModel 인스턴스의 수명 주기를 관리하는 메커니즘 역할을 하는 `ViewModelStoreOwner`에 범위가 지정될 수 있습니다. 
`ViewModelStoreOwner`는 Activity, Fragment, Navigation graph, Navigation graph 내의 목적지 또는 개발자가 정의한 Custom Owner가 될 수 있습니다.

Jetpack 라이브러리는 다양한 사용 사례에 맞춰 ViewModel의 범위를 지정할 수 있는 다용도 옵션을 제공합니다.
포괄적인 개요를 위해 아래 표시된 시각적 가이드도 제공하는 [ViewModel APIs cheat sheet](https://developer.android.com/topic/libraries/architecture/viewmodel/viewmodel-cheatsheet)를 참조하세요.

![viewmodels-apis.png](viewmodels-apis.png)

### 요약
Jetpack ViewModel은 UI 관련 데이터를 저장하고 관리하도록 설계된 핵심 구성 요소로, 구성 변경 시에도 원활하게 데이터가 유지되도록 보장합니다. 이는 수명 주기를 인식하고 MVVM 아키텍처 패턴과 효과적으로 통합되어 상태 관리를 단순화하고 화면 회전과 같은 이벤트 중에도 데이터를 보존하여 전반적인 개발 경험을 향상시킵니다.


<deflist collapsible="true" default-state="collapsed">
<def title="Q) ViewModel은 구성 변경 시 데이터를 어떻게 유지하며, onSaveInstanceState()를 사용하여 상태를 저장하는 것과 어떻게 다른가요?">

**ViewModel**: 화면 회전 같은 구성 변경 시, 데이터를 메모리에 그대로 유지시켜 UI가 즉시 복원되게 합니다.

**onSaveInstanceState()**: 앱이 백그라운드에서 시스템에 의해 종료되는 프로세스 데스 시, 데이터를 디스크에 직렬화하여 저장하고, 나중에 앱이 재시작될 때 이 데이터를 복원할 수 있게 합니다.

**Jetpack ViewModel 동작 원리**
1. Activity가 생성될 때, 안드로이드 프레임워크는 `ViewModelStore`라는 보관함을 생성합니다. (Activity가 `ViewModelStoreOwner`)
2. `ViewModelProvider`를 통해 `ViewModel`를 요청하면, `ViewModel` 인스턴스가 생성되어 이 `ViewModelStore`에 저장됩니다.
3. 사용자가 화면을 회전하면, Activity 인스턴스는 파괴되고 재생성됩니다.
4. 하지만 프레임워크는 이것이 일시적인 파괴임을 알기에 `ViewModelStore`는 파괴되지 않고 그대로 유지합니다.
5. 새로 생성된 Activity가 `ViewModelProvider`를 통해 `ViewModel`을 다시 요청하면, 프레임워크는 `ViewModelStore`에 이미 저장된 `ViewModel` 인스턴스를 즉시 반환합니다.

**onSaveInstanceState 동작 원리**
1. 화면 회전 또는 앱이 백그라운드로 전환될 때처럼 시스템이 Activity를 파괴할 가능성이 생기면, onSaveInstanceState() 콜백이 호출됩니다.
2. 개발자는 이 메서드 안에서 복원해야 할 최소한의 데이터를 Bundle 객체에 put 합니다.
3. 시스템은 이 Bundle을 직렬화하여 안전한 곳(디스크)에 저장합니다.
4. 이후 Activity가 다시 생성될 때, 시스템은 저장했던 Bundle을 onCreate의 파라미터로 전달합니다.

</def>
<def title="Q) ViewModelStoreOwner의 목적은 무엇이며, 동일한 Activity 내에서 여러 Fragment 간에 ViewModel을 어떻게 공유할 수 있나요?">

ViewModel이 언제까지 살아있어야 하는지 그 생명주기를 결정하는 목적입니다. Activity나 Fragment가 이 Owner 역할을 하며, Owner가 파괴될 때 ViewModel의 onCleared가 호출됩니다.

Fragment간 ViewModel 공유 방법은 두 Fragment가 동일한 ViewModelStoreOwner를 바라보게 만들면 됩니다.
가장 쉬운 방법은 부모 Activity를 공유 Owner로 삼는 것입니다.

</def>
<def title="Q) UI 상태 관리를 위해 ViewModel 내에서 StateFlow 또는 LiveData를 사용하는 것의 장점과 잠재적인 단점은 무엇인가요?">

**StateFlow**
1. 장점
   - Kotlin 코루틴 생태계와 완벽하게 통합되어 있어, suspend 함수와 자연스럽게 연동됩니다.
   - Flow 연산자들(map, filter, combind 등)을 활용한 풍부한 데이터 변환이 가능합니다.
   - hot 스트림으로, 구독자가 없어도 상태를 유지합니다.
   - 초기값 보장으로 null 안정성
   - .vlaue 프로퍼티로 현재 상태를 동기적으로 읽을 수 있음
   - 중복된 값은 자동으로 필터링해서 리컴포지션 방지
   - KMM 에서 사용 가능 (Kotlin 이니까)
2. 단점
   - 생명주기 미인식: Activity/Fragment의 생명주기를 자동으로 인식하지 못한다.

**LiveData**
1. 장점
   - 생명주기 인식
   - 메모리 누수 방지
   - 간단한 사용법
   - databinding 통합 (xml 레이아웃에서 직접 바인딩 가능)
2. 단점
   - 안드로이드 프레임워크 종속성으로 테스트 힘듦
   - 복잡한 데이터 변환 불가
   - null 허용

</def>
</deflist>