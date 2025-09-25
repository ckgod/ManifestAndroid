# Q9) Fragment 생명주기

## Fragment 생명주기

각 Fragment 인스턴스는 자신이 연결된 Activity의 생명주기와 별개로 고유한 생명주기를 가집니다.
사용자가 앱과 상호작용함에 따라, Fragment는 추가되거나 제거되거나 화면에 나타나거나 사라지는 등 다양한 생명주기 상태를 거칩니다. 
이러한 생명주기 단계에는 생성, 시작, 가시화, 활성화가 포함되며, 더 이상 필요 없을 때는 중지되거나 소멸되는 상태로 전환됩니다. 이러한 전환을 관리하면 Fragment가 리소스를 효과적으로 처리하고, UI 일관성을 유지하며, 사용자 동작에 원할하게 응답할 수 있습니다. 

Android의 Fragment 생명주기는 Activity 생명주기와 매우 유사하지만, Fragment 고유의 몇 가지 추가 메서드와 동작을 도입합니다.

![fragment_lifecycle.png](fragment_lifecycle.png)

1. **`onAttach()`**: `Fragment`가 부모 `Activity`에 연결될 때 호출되는 첫 번째 콜백입니다. `Fragment`가 이제 연결되어 `Activity context`와 상호 작용할 수 있습니다.
2. **`onCreate()`**: `Fragment`를 초기화하기 위해 호출됩니다. 이 시점에서 `Fragment`는 생성되었지만, `UI`는 아직 생성되지 않았습니다. 일반적으로 필수 구성 요소를 초기화하거나 저장된 상태를 복원하는 곳입니다.
3. **`onCreateView()`**: `Fragment`의 `UI`가 처음 그려질 때 호출됩니다. 이 메서드에서 `Fragment` 레이아웃의 루트 뷰를 반환합니다. `LayoutInflater`를 사용하여 `Fragment`의 레이아웃을 인플레이트(inflate)하는 곳입니다.
4. **`onViewStateRestored()`**: `Fragment`의 뷰 계층이 생성되고 저장된 상태가 뷰에 복원된 후 호출됩니다.
5. **`onViewCreated()`**: `Fragment`의 뷰가 생성된 후 호출되는 메서드입니다. `UI` 구성 요소를 설정하고 사용자 상호 작용을 처리하는 데 필요한 모든 로직을 설정하는 데 자주 사용됩니다.
6. **`onStart()`**: `Fragment`가 사용자에게 표시됩니다. 이는 `Activity`의 `onStart()` 콜백과 동일하며, `Fragment`가 이제 활성화되었지만 아직 포그라운드에 있지 않은 상태입니다.
7. **`onResume()`**: `Fragment`가 이제 완전히 활성화되어 포그라운드에서 실행 중이며, 상호 작용이 가능합니다. 이 메서드는 `Fragment`의 `UI`가 완전히 표시되고 사용자가 상호 작용할 수 있을 때 호출됩니다.
8. **`onPause()`**: `Fragment`가 더 이상 포그라운드에 있지 않지만 여전히 표시될 때 호출됩니다. `Fragment`가 포커스를 잃으려고 하므로, `Fragment`가 포그라운드에 없을 때 계속되어서는 안 되는 작업을 일시 중지해야 합니다.
9. **`onStop()`**: `Fragment`가 더 이상 표시되지 않습니다. `Fragment`가 화면에 없는 동안 계속될 필요가 없는 작업을 중지하는 곳입니다.
10. **`onSaveInstanceState()`**: `Fragment`가 파괴되기 전에 `UI` 관련 상태 데이터를 저장하여 나중에 복원할 수 있도록 호출됩니다.
11. **`onDestroyView()`**: `Fragment`의 뷰 계층이 제거될 때 호출됩니다. 메모리 누수를 방지하기 위해 어댑터를 지우거나 참조를 null로 설정하는 등 뷰와 관련된 리소스를 정리해야 합니다.
12. **`onDestroy()`**: `Fragment` 자체가 파괴될 때 호출됩니다. 이 시점에서 모든 리소스를 정리해야 하지만, `Fragment`는 여전히 부모 `Activity`에 연결되어 있습니다.
13. **`onDetach()`**: `Fragment`가 부모 `Activity`에서 분리되어 더 이상 연결되지 않습니다. 이는 마지막 콜백이며, `Fragment`의 생명주기가 완료됩니다.

## 요약
Android 앱에서 Fragment 생명 주기를 이해하는 것은 리소스를 효과적으로 관리하고, 구성 변경을 처리하며, 원활한 사용자 경험을 보장하는 데 중요합니다.

[Fragment Lifecycle](https://developer.android.com/guide/fragments/lifecycle)

> Q) `onCreateView()` 및 `onDestroyView()`의 목적은 무엇이며, 이 메서드에서 뷰 관련 리소스를 적절히 처리하는 것이 왜 중요한가요?

#### A) {collapsible="true"}
`onCreateView()`와 `onDestroyView()`는 Android Fragment의 생명주기 메서드로, 뷰의 생성과 소멸을 관리하는 핵심적인 역할을 합니다.
##### onCreateView()의 목적
`onCreateView()`는 Fragment의 UI를 생성하는 메서드입니다. 이 메서드에서:
- Fragment의 레이아웃을 인플레이트(inflate)합니다
- View 객체를 반환하여 Fragment의 UI 계층구조를 정의합니다
- Fragment가 화면에 표시될 때 호출됩니다

```kotlin
override fun onCreateView(
    inflater: LayoutInflater,
    container: ViewGroup?,
    savedInstanceState: Bundle?
): View? {
    return inflater.inflate(R.layout.fragment_example, container, false)
}
```
##### onDestroyView()의 목적
`onDestroyView()`는 Fragment의 뷰가 소멸될 때 호출됩니다. 이 메서드에서:
- 뷰와 관련된 리소스를 정리합니다
- 메모리 누수를 방지합니다
- Fragment가 백스택에서 제거되거나 교체될 때 호출됩니다

##### 뷰 관련 리소스 적절한 처리의 중요성
1. 메모리 누수 방지
Fragment가 소멸되어도 뷰에 대한 참조가 남아있으면 가비지 컬렉션이 되지 않아 메모리 누수가 발생합니다.

```kotlin
class ExampleFragment : Fragment() {
    private var binding: FragmentExampleBinding? = null
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        binding = FragmentExampleBinding.inflate(inflater, container, false)
        return binding?.root
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        binding = null // 중요: 바인딩 참조 해제
    }
}
```

##### 2. 리스너 및 콜백 해제
등록된 리스너들이 제대로 해제되지 않으면 메모리 누수의 원인이 됩니다.

```kotlin
override fun onDestroyView() {
    super.onDestroyView()
    // 리스너 해제
    someButton.setOnClickListener(null)
    // 옵저버 해제
    viewModel.data.removeObservers(viewLifecycleOwner)
    binding = null
}
```

##### 3. 백그라운드 작업 정리
진행 중인 비동기 작업들을 정리하여 불필요한 작업을 방지합니다.

##### Fragment 생명주기에서의 위치 {#135135}

Fragment 생명주기에서 이 메서드들의 위치:
1. `onAttach()` → `onCreate()` → **`onCreateView()`** → `onViewCreated()` → `onStart()` → `onResume()`
2. `onPause()` → `onStop()` → **`onDestroyView()`** → `onDestroy()` → `onDetach()`

이러한 적절한 리소스 관리는 안정적인 앱 성능과 메모리 효율성을 보장하는 Android 개발의 핵심 원칙입니다.