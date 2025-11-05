# Q12) State hoisting

## State hoisting의 이점은 무엇인가요?

[State hoisting](https://developer.android.com/develop/ui/compose/state-hoisting)은 composable에서 더 높은 수준의 컴포넌트나 부모로 state를 이동하는 것을 의미합니다. 
이 패턴은 현재 state 값과 state를 업데이트하는 람다를 composable에 매개변수로 전달하는 것을 포함합니다. 
State hoisting은 단방향 데이터 흐름(unidirectional data flow) 원칙을 따르므로, UI를 더 쉽게 관리하고 확장할 수 있습니다.

State hoisting에서:
* State는 부모 composable에서 관리됩니다.
* 이벤트나 트리거(예: onClick, onValueChange)는 자식에서 부모로 전달되어 state를 업데이트합니다. 
* 업데이트된 state는 매개변수로 다시 자식에게 전달되어 단방향 데이터 흐름을 생성합니다.

### 예시
아래 예시를 통해 State hoisting이 어떻게 작동하는지 살펴보겠습니다.

```Kotlin
@Composable
fun Parent() {
    var sliderValue by remember { mutableStateOf(0f) }

    SliderComponent(
        value = sliderValue,
        onValueChange = { sliderValue = it }
    )
}

@Composable
fun SliderComponent(value: Float, onValueChange: (Float) -> Unit) {
    Slider(value = value, onValueChange = onValueChange)
}
```

위 예시에서 `SliderComponent` composable만 살펴보면, 어떠한 내부 state도 관리하지 않는 것을 볼 수 있습니다. 
그 결과, 이 컴포넌트는 동일한 기능을 유지하면서 다양한 목적의 여러 화면에서 재사용될 수 있습니다.
이와 같은 composable 함수를 **stateless**라고 합니다.

하지만 아래와 같은 함수는 어떨까요?

```Kotlin
@Composable
fun SliderComponent() {
    var sliderValue by remember { mutableStateOf(0f) }

    Slider(value = sliderValue, onValueChange = { sliderValue = it })
}
```

이 예시에서 `SliderComponent`는 자체 내부 state를 관리합니다. 
이는 호출 지점에서 어떤 입력 매개변수도 필요로 하지 않고 모든 것을 내부적으로 처리하기 때문에 사용하기 쉽습니다. 
그러나 `"Hello, $sliderValue"`와 같은 메시지로 현재 slider 값을 표시해야 하는 요구 사항이 발생하면 해당 경우를 처리하기 위해 완전히 별도의 composable 함수를 생성해야 합니다.

이러한 composable을 **stateful**이라고 하며, 보시다시피 재사용성이 떨어지는 경향이 있습니다.

### State hoisting의 주요 이점 {#sh1441}

* **향상된 재사용성**: State hoisting을 통해 composable은 stateless하고 재사용 가능해집니다. state와 이벤트 콜백을 전달함으로써, 동일한 composable을 특정 구현에 묶이지 않고 다양한 화면이나 컨텍스트에서 사용할 수 있습니다.
* **간소화된 테스트**: stateless composable은 동작이 매개변수로 전달된 state에 전적으로 의존하므로 테스트하기 쉽습니다. 이는 예측 가능하게 만들고 명확한 테스트 시나리오를 가능하게 합니다.
* **향상된 관심사 분리**: state 관리 로직을 부모 composable 또는 ViewModel로 이동함으로써, State hoisting은 UI 요소가 인터페이스 렌더링에 집중하도록 합니다. 이러한 분리는 비즈니스 로직과 UI 코드를 명확하게 구분하여 유지보수성을 향상시킵니다.
* **단방향 데이터 흐름 지원**: State hoisting은 Jetpack Compose의 단방향 데이터 흐름(unidirectional data flow) 아키텍처와 일치하여 state가 단일 진실의 원천(single source of truth)에서 흐르도록 보장합니다. 이는 여러 소스가 동일한 state를 관리하려고 시도하여 발생하는 예기치 않은 동작의 가능성을 줄입니다.
* **강화된 state 관리**: State hoisting을 사용하면 ViewModel 또는 부모 composable과 같은 상위 수준 컨테이너에서 state를 중앙 집중화할 수 있습니다. 이를 통해 복잡한 UI 흐름을 더 쉽게 관리하고 인스턴스 state 저장 또는 state 복원 관리와 같은 작업을 처리할 수 있습니다.

### 요약
State hoisting은 더 깔끔하고, 모듈화되며, 테스트 가능한 코드를 촉진합니다. 
이는 단방향 데이터 흐름(unidirectional data flow)을 지원하여 재사용성과 유지보수성을 모두 향상시킵니다. 
composable을 stateless하게 유지함으로써 개발자는 변화하는 애플리케이션 요구 사항에 적응하는 유연한 UI 컴포넌트를 만들 수 있습니다.

#### Q1
> State hoisting은 composable 함수의 재사용성과 테스트 용이성을 어떻게 향상시키나요?

##### A) {#A113 collapsible="true"}
State hoisting는 관심사 분리를 통해 컴포저블을 Stateless하게 만듭니다. 
1. 재사용성: 상태 관리 로직이 분리되면서, 컴포저블은 UI 렌더링에만 집중합니다. 덕분에 동일한 UI를 어떤 상태의 소스와도 결합하여 재사용할 수 있습니다. 
2. 테스트 용이성: UI와 로직을 따로 테스트할 수 있게 됩니다. UI(컴포저블)는 특정 상태를 주입하고 UI 결과만 확인하면 되고, 상태 로직(ViewModel 등)은 Compose 런타임 없이도 유닛 테스트로 검증할 수 있습니다.

#### Q2
> 어떤 시나리오에서 State hoisting을 피하고 대신 composable 내부에 state를 유지할까요?

##### A) {#A1213 collapsible="true"}
UI 전용 상태
- 애니메이션 상태(비즈니스 로직과 무관)
컴포저블과 강하게 결합된 상태
- LazyList의 스크롤 위치
상위 컴포저블에 부담을 주지 않아야 할 때
- 대표적으로 TextField의 중간 입력 값
TextField의 포커스 상태
- 포커스 상태는 TextField의 내부 동작

결론적으로 상태가 컴포넌트의 외부에서 관심을 가져야 하는가?를 기준으로 판단.
