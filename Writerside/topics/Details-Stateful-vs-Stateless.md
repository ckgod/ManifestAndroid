# Details: Stateful vs. Stateless

## Stateful vs. Stateless, State Hoisting 이해하기
State Hoisting은 상태 관리 책임을 호출 지점으로 이동시켜 Stateful `Composable`을 Stateless `Composable`로 변환하는 데 사용되는 디자인 패턴입니다. 

이 접근 방식은 일반적으로 `remember`를 사용하여 관리되는 내부 상태 변수를 현재 상태 값과 상태를 업데이트하는 콜백 함수라는 두 개의 매개변수로 대체합니다. 
이러한 책임 분리는 더 깔끔하고 재사용 가능하며 테스트 가능한 `Composable` 함수를 촉진합니다.
상태 관리 책임을 호출자에게 넘김으로써, `Composable`은 Stateless가 되어 재사용, 테스트 및 유지보수가 더 쉬워집니다.

예를 들어, `MyTextField` `Composable`은 부모로부터 직접 텍스트 값과 사용자 입력을 처리하기 위한 콜백을 받아 명확한 데이터 흐름을 보장할 수 있습니다.
이러한 분리는 `Composable`이 UI 렌더링에만 집중하도록 유지하면서 상태 관리는 호출 컴포넌트에 맡겨 모듈성을 향상하고 복잡성을 줄입니다.

![state-hoisting.png](state-hoisting.png)

다음으로, 예시 코드를 사용하여 Stateful 및 Stateless `Composable` 함수의 차이점을 살펴보겠습니다. 
명확성을 높이기 위해 진행하면서 위 그림을 참조하세요.

사용자 입력을 처리하도록 설계된 `MyTextField`라는 사용자 정의 텍스트 필드를 생각해 봅시다. `MyTextField`를 Stateful `Composable` 함수로 구현하는 방법은 다음과 같습니다.

```Kotlin
@Composable
fun HomeScreen() { 
    MyTextField()
}

@Composable
fun MyTextField() {
    val (value, onValueChanged) = remember { mutableStateOf("") }
    TextField(value = value, onValueChange = onValueChanged)
}
```

위 코드 예시에서 `MyTextField`는 `remember` 컴포저블 함수를 사용하여 내부 상태를 관리합니다. 이 함수는 상태를 메모리에 저장하고 입력 변경 사항을 추적합니다. 
이러한 설계로 `MyTextField`는 자체 상태를 독립적으로 처리하므로 Stateful `Composable`이 됩니다. 

이 접근 방식에는 장단점이 있습니다.

장점으로는 호출 지점(`HomeScreen`)이 상태를 관리할 필요가 없어 구현이 단순해진다는 점입니다. 
그러나 단점은 유연성이 감소한다는 것입니다. 
`MyTextField`가 내부적으로 상태를 관리하기 때문에 외부에서 해당 동작을 제어하거나 사용자 지정하기가 더 어려워집니다.
이는 `Composable`을 다른 컨텍스트에서 재사용하기 어렵게 만들 수 있습니다.

이러한 제한 사항을 해결하면서 동일한 기능을 달성하는 대체 접근 방식을 살펴보겠습니다.

```Kotlin
@Composable
fun HomeScreen() {
    val (value, onValueChanged) = remember { mutableStateOf("") }

    MyTextField(
        value = value,
        onValueChanged = onValueChanged
    )
}

@Composable
fun MyTextField(
    value: String,
    onValueChanged: (String) -> Unit
) {
    TextField(value = value, onValueChange = onValueChanged)
}
```

이 예시에서 `MyTextField`는 `Stateless Composable`로 구현되어 매개변수를 통해 변경 사항을 반영하고 상태 관리를 호출 지점(`HomeScreen`)에 위임합니다.
이 접근 방식은 이전 Stateful 구현보다 코드가 약간 더 길어질 수 있지만, 중요한 이점인 향상된 재사용성을 제공합니다.

`MyTextField`를 Stateless로 유지함으로써, 다른 컨텍스트에서 쉽게 재사용하고 다양한 사용 사례에 맞게 조정하여 더 깔끔하고 모듈화된 코드를 촉진할 수 있습니다.
이 접근 방식은 `State Hoisting`이라고 알려져 있으며, `MyTextField`와 같은 Callee에서 `HomeScreen`과 같은 Caller로 상태 관리가 올라갑니다. 

UI 계층 구조에서 상태를 더 높은 곳에서 관리함으로써 이 기술은 다양한 컴포넌트에서 더 유연하고 재사용 가능하며 제어되는 상태 관리를 가능하게 합니다.
위에 제시된 Stateless 예시를 바탕으로 사용자가 숫자를 입력하는 것을 제한하는 텍스트 필드를 만들려는 시나리오를 생각해 보세요. 
이는 Stateless 접근 방식의 적응성을 보여주며, 원래 `Composable`을 수정하지 않고도 쉽게 사용자 정의할 수 있습니다.

아래 예시와 같이 이 기능을 구현할 수 있습니다.

```Kotlin
@Composable
fun HomeScreen() {
    val (value, onValueChanged) = remember { mutableStateOf("") }
    val processedValue by remember(value) {
        derivedStateOf {
            value.filter { !it.isDigit() }
        }
    }

    MyTextField(
        value = processedValue,
        onValueChanged = onValueChanged
    )
}

@Composable
fun MyTextField(
    value: String,
    onValueChanged: (String) -> Unit
) {
    TextField(value = value, onValueChange = onValueChanged)
}
```

또한, `MyTextField`는 다양한 방식으로 재사용될 수 있으며, 특정 요구 사항에 맞게 사용자 정의될 수 있습니다. 
이러한 유연성은 `State Hoisting`의 핵심 이점을 강조합니다. 

즉, 외부 제어 및 사용자 정의를 가능하게 하여 `Composable` 함수의 재사용성을 향상시킵니다. 
결과적으로 컴포넌트는 내부 변경 없이 다른 컨텍스트에 적응할 수 있게 되어 코드베이스를 더 깔끔하고 유지보수하기 쉽게 만듭니다.