# Q41) Compose 접근성

## Jetpack Compose에서 접근성을 어떻게 보장하나요? {#how-to-ensure-accessibility}

[Jetpack Compose의 접근성](https://developer.android.com/develop/ui/compose/accessibility)을 다룬다는 것은, 스크린 리더 같은 보조 기술이 UI 컴포넌트를 손쉽게 해석하고 상호작용할 수 있도록 컴포넌트를 설계하는 일을 뜻합니다. Compose는 선언형 UI 모델을 유지하면서도 접근성 기능을 구현하기 좋은 유연한 API들을 제공합니다.

### Semantics Modifier {#semantics-modifier}

Compose 접근성 시스템의 핵심은 **semantics modifier** 입니다. UI 요소가 접근성 서비스에 어떻게 해석되어야 할지를 기술할 수 있게 해 줍니다.

```kotlin
Modifier.semantics { contentDescription = "Send Button" }
```
{title="SemanticsModifier.kt"}

이 modifier 가 보조 도구에게 contentDescription, role, custom action 같은 메타데이터를 전달합니다. 다만 `Text`, `Button`, `Icon` 같은 대부분의 컴포저블은 이미 내장 시맨틱을 가지고 있으므로, `semantics` 의 직접 사용은 보통 커스텀 컴포넌트에 한정됩니다.

### 이미지·아이콘의 contentDescription {#content-description}

`contentDescription` 파라미터는 `Image` 와 `Icon` 컴포저블의 기본 접근성 파라미터입니다. 시각적 콘텐츠에 텍스트 컨텍스트를 부여해 줍니다.

```kotlin
Icon(
    imageVector = Icons.Default.Send,
    contentDescription = "Send"
)
```
{title="IconWithContentDescription.kt"}

장식용 이미지(decorative image)라면 `null` 을 전달해 접근성 서비스의 트리에서 제외할 수 있습니다.

```kotlin
Image(painter = painterResource(id = R.drawable.divider), contentDescription = null)
```
{title="DecorativeImage.kt"}

### 그룹 콘텐츠를 위한 시맨틱 병합 {#merging-semantics}

여러 요소를 하나의 논리 단위로 보여 줘야 할 때는 `Modifier.clearAndSetSemantics {}` 또는 `Modifier.semantics(mergeDescendants = true)` 로 묶어서 접근성 측면에서 한 묶음이 되도록 만들 수 있습니다.

```kotlin
Column(
    modifier = Modifier.semantics(mergeDescendants = true) {}
) {
    Text("Flight: NZ123")
    Text("Departure: 10:30 AM")
}
```
{title="MergedSemantics.kt"}

이 설정은 보조 기술이 콘텐츠를 한 항목으로 읽도록 만들어 줍니다.

### 커스텀 접근성 액션 {#custom-actions}

스크린 리더나 다른 도구를 사용하는 사용자를 위해 커스텀 액션을 추가할 수 있습니다.

```kotlin
Modifier.semantics {
    onClick("Double tap to bookmark") {
        // 클릭 처리
        true
    }
}
```
{title="CustomSemanticsAction.kt"}

이렇게 하면 보조 기술 사용자에게 더 설명적이고 상호작용 가능한 UI 경험을 제공할 수 있습니다.

### 접근성 테스트 {#testing-accessibility}

[Accessibility Scanner](https://support.google.com/accessibility/android/answer/6376570?hl=en)나 Compose UI 테스트의 시맨틱 단언으로 접근성 라벨, 역할, 계층을 검증할 수 있습니다.

```kotlin
composeTestRule.onNodeWithContentDescription("Send").assertExists()
```
{title="ComposeAccessibilityTest.kt"}

### 요약 {#summary}

<tldr>

Jetpack Compose는 `semantics`, `contentDescription`, `mergeDescendants` 같은 구조화된 API를 제공해 접근성을 갖춘 UI를 구현할 수 있게 해 줍니다. 시각적 요소에 적절한 메타데이터를 부여하고 관련 콘텐츠를 그룹화함으로써, 보조 기술에 의존하는 사용자까지 포함한 더 넓은 사용자층이 앱을 자연스럽게 사용할 수 있도록 만들 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) semantics modifier 의 목적은 무엇인가요?">

`semantics` modifier 의 본질은 **Compose 가 만드는 UI 트리 위에 별도의 "의미 트리(semantics tree)"를 정의** 하는 것입니다. 화면이 그려지는 시각 트리는 픽셀과 레이아웃을 결정하지만, 보조 기술(스크린 리더, 음성 제어, 스위치 디바이스 등) 은 픽셀이 아니라 의미 트리를 기준으로 동작합니다. semantics modifier 는 그 의미 트리에 어떤 요소가 어떤 역할(role)을 하고, 어떤 라벨(label)을 가지며, 어떤 액션(action)에 반응하는지를 기록해 두는 도구입니다.

대부분의 표준 컴포저블(`Text`, `Button`, `Icon`, `TextField` 등)은 이미 적절한 시맨틱을 자동으로 부여합니다. 그래서 일반적인 경우에는 개발자가 `semantics` modifier 를 직접 적을 필요가 거의 없습니다. 직접 작성이 필요해지는 자리는 두 가지로 압축됩니다. 첫째, **시각적으로는 표현되지만 표준 컴포저블이 없는 커스텀 컴포넌트**(예: 직접 그린 progress bar, 커스텀 토글)에 라벨이나 role 을 부여해야 할 때입니다. 둘째, **여러 요소가 함께 의미를 만들어 내는 경우**(예: 카드 안의 제목 + 메타데이터)에 `mergeDescendants = true` 또는 `clearAndSetSemantics` 로 의미 트리를 다듬어야 할 때입니다.

또 한 가지 자주 만나는 사용처는 **테스트** 입니다. 화면 전체에서 특정 노드를 정확히 찾기 위해 `Modifier.testTag("...")` 와 함께 시맨틱 라벨을 부여하면, UI 테스트가 안정적으로 동작합니다. 결국 semantics modifier 는 "보조 기술과 테스트 도구를 위한 추가 채널" 이라고 보면 자연스럽고, 이 채널이 잘 정리된 화면일수록 접근성 점수와 테스트 안정성이 함께 올라갑니다.

</def>
<def title="Q) Compose에서 여러 UI 요소를 하나의 접근성 노드처럼 동작하게 만들려면 어떻게 해야 하나요?">

가장 자주 쓰이는 두 가지 도구는 `Modifier.semantics(mergeDescendants = true)` 와 `Modifier.clearAndSetSemantics { ... }` 입니다. 전자는 자식들의 시맨틱을 부모 노드 안으로 **합쳐 줍니다**. 즉 자식들이 가진 라벨·역할 정보가 모두 부모 한 노드에 결합되어, 보조 기술이 그 그룹을 단일 항목으로 읽게 됩니다. 본문 예시처럼 항공편 정보처럼 한 카드가 여러 텍스트로 구성되어 있을 때 이 modifier 를 부모 컬럼에 적용하면, 스크린 리더가 "Flight: NZ123, Departure: 10:30 AM" 을 한 번에 읽어 줍니다.

후자(`clearAndSetSemantics`)는 자식들의 시맨틱을 **모두 지우고 부모에 새 시맨틱을 설정** 합니다. 자식들이 너무 자세한 시맨틱을 가지고 있어 부모 단위에서 단순화하고 싶을 때, 또는 부모가 의미 단위로 명확한 라벨을 가져야 할 때 사용합니다. 예를 들어 카드 안의 여러 텍스트가 각각 시맨틱 라벨을 가지고 있더라도, 사용자에게는 "이 카드는 새 메시지입니다" 라고 한 줄로 들려 주고 싶다면 `clearAndSetSemantics { contentDescription = "새 메시지" }` 로 정리할 수 있습니다.

선택 기준을 단순화하면 **자식들의 정보가 그대로 의미 있게 합쳐지는 경우** 에는 `mergeDescendants = true`, **부모 단위로 시맨틱을 새로 정의해야 하는 경우** 에는 `clearAndSetSemantics` 가 자연스럽습니다. 추가로 그룹 노드는 클릭 가능한 영역으로도 다뤄지는 경우가 많으므로, `Modifier.clickable { ... }.semantics(mergeDescendants = true) { }` 패턴으로 한 번의 더블 탭에 카드 전체가 동작하도록 만들면 보조 기술 사용자에게도 자연스러운 인터랙션이 됩니다.

</def>
</deflist>
