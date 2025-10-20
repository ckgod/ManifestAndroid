# Details: Fragment Result API

어떤 경우, Fragment는 다른 Fragment 또는 Fragment와 호스트 Activity 간에 **한 번만 사용하는 값**을 전달해야 합니다. 
예를 들어, QR 코드 스캔 Fragment는 스캔된 데이터를 이전 Fragment로 다시 보내야 할 수 있습니다.

[**Fragment**](https://developer.android.com/jetpack/androidx/releases/fragment) 버전 1.3.0 이상부터,
각 `FragmentManager`는 `FragmentResultOwner`를 구현하여, Fragment들이 서로에 대한 직접적인 참조 없이 결과 리스너를 통해 통신할 수 있도록 합니다.
이는 느슨한 결합을 유지하면서 데이터 전달을 간소화합니다.

**Fragment B(송신자)** 에서 **Fragment A(수신자)** 로 데이터를 전달하려면 다음 단계를 따르세요.

1.  Fragment A(결과를 수신하는 Fragment)에 결과 리스너를 설정합니다.
2.  동일한 `requestKey`를 사용하여 Fragment B에서 결과를 전송합니다.

## Fragment A에서 결과 리스너 설정하기
Fragment A는 `setFragmentResultListener()`를 사용하여 리스너를 등록해야 하며, `STARTED` 상태가 될 때 결과를 수신하도록 보장합니다.

```kotlin
class FragmentA : Fragment() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Register listener to receive results
        setFragmentResultListener("requestKey") { _, bundle ->
            val result = bundle.getString("bundleKey")
            // Handle the received result
        }
    }
}
```

`setFragmentResultListener("requestKey")`는 특정 `requestKey`에 대한 리스너를 등록합니다. 콜백은 Fragment가 `STARTED` 상태가 될 때 실행됩니다.

## Fragment B에서 결과 전송하기
Fragment B는 `setFragmentResult()`를 사용하여 결과를 전송하며, Fragment A가 활성화될 때 데이터를 검색할 수 있도록 보장합니다.

```kotlin
class FragmentB : Fragment() {

    private lateinit var button: Button

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        button = view.findViewById(R.id.button)
        button.setOnClickListener {
            val result = "result"
            // Send the result to FragmentA
            setFragmentResult("requestKey", bundleOf("bundleKey" to result))
        }
    }
}
```

`setFragmentResult("requestKey", bundleOf("bundleKey" to result))`는 지정된 키를 사용하여 FragmentManager에 결과를 저장합니다.
Fragment A가 활성화되지 않은 경우, 결과는 Fragment A가 재개되고 리스너를 등록할 때까지 저장됩니다.

## Fragment 결과의 동작 방식
*   **키당 단일 리스너**: 각 키는 한 번에 하나의 리스너와 하나의 결과만 가질 수 있습니다.
*   **보류 중인 결과는 덮어쓰기됩니다**: 리스너가 활성화되기 전에 여러 결과가 설정되면 최신 결과만 저장됩니다.
*   **결과는 소비된 후 지워집니다**: Fragment가 결과를 수신하고 처리하면 해당 결과는 FragmentManager에서 제거됩니다.
*   **백 스택의 Fragment는 결과를 수신하지 않습니다**: Fragment는 결과를 수신하려면 백 스택에서 제거되고 `STARTED` 상태여야 합니다.
*   **`STARTED` 상태의 리스너는 즉시 트리거됩니다**: Fragment B가 결과를 설정할 때 Fragment A가 이미 활성화되어 있으면 리스너가 즉시 실행됩니다.

## 요약
Fragment Result API는 직접적인 참조 없이 Fragment 간에 한 번만 사용하는 값을 전달하는 것을 간소화합니다.
FragmentManager를 활용하여 결과는 수신 Fragment가 활성화될 때까지 안전하게 저장되어, 분리되고 라이프사이클을 인식하는 통신 메커니즘을 보장합니다.
이 접근 방식은 QR 코드 스캔, 사용자 입력 대화 상자 또는 양식 제출과 같은 다양한 시나리오에서 유용하며, Fragment 기반 탐색을 보다 효율적이고 유지보수 가능하게 만듭니다.