# Q38) Compose Preview

## Compose Preview는 어떻게 동작하고 어떻게 활용하나요? {#how-preview-works}

Jetpack Compose의 큰 장점 중 하나는 Android Studio가 제공하는 [@Preview](https://developer.android.com/develop/ui/compose/tooling/previews) 기능입니다. 전체 프로젝트를 빌드하지 않고도 **UI 컴포넌트를 점진적으로 만들고 시각화** 할 수 있어, UI 변경을 빠르게 검증할 수 있고 개발 흐름도 한층 매끄러워집니다.

[Compose UI Tooling preview 라이브러리](https://developer.android.com/develop/ui/compose/tooling)는 다양한 어노테이션을 제공해 Android Studio에서의 프리뷰 경험을 풍부하게 만들어 줍니다.

### @Preview로 컴포저블 렌더링하기 {#using-preview}

`@Preview` 어노테이션은 Compose 프리뷰 시스템의 기본입니다. 어떤 컴포저블 함수에든 적용할 수 있고, 한 함수에 여러 개의 `@Preview` 를 붙일 수도 있어 같은 컴포저블을 다양한 구성이나 디바이스로 시각화할 수 있습니다.

```kotlin
@Preview(name = "light mode")
@Preview(name = "dark mode", uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun MyPreview() {
    MaterialTheme {
        Text(
            text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            color = if (isSystemInDarkTheme()) {
                Color.White
            } else {
                Color.Yellow
            }
        )
    }
}
```
{title="SimplePreview.kt"}

`@Preview` 가 Android Studio에 해당 컴포저블을 **Preview 창에 렌더링** 하라고 알려 주며, 여러 프리뷰를 만들면 다양한 UI 상태를 한 번에 시각화할 수 있습니다.

### Preview 커스터마이즈 {#customizing-previews}

`@Preview` 는 다양한 파라미터로 커스터마이즈할 수 있습니다.

```kotlin
@Preview(
    name = "Dark Mode Preview",
    showBackground = true,
    backgroundColor = 0xFF000000,
    uiMode = Configuration.UI_MODE_NIGHT_YES,
    device = Devices.PIXEL_4_XL,
)
@Composable
fun DarkModePreview() {
    Greeting(name = "skydoves")
}
```
{title="CustomPreview.kt"}

자주 사용하는 파라미터는 다음과 같습니다.

- **name**: 프리뷰에 이름을 부여합니다. 한 컴포저블에 여러 프리뷰를 둘 때 이름이 헷갈리지 않게 해 줍니다.
- **showBackground**: 컴포저블 뒤에 배경을 그립니다. 기본 배경이 투명이라 IDE 배경과 색이 같으면 컴포넌트가 잘 안 보일 수 있어 활성화를 권장합니다.
- **backgroundColor**: 커스텀 배경색을 지정합니다.
- **uiMode**: 다크 모드 같은 시스템 모드를 적용합니다.
- **device**: `Devices.PIXEL_4_XL` 처럼 특정 디바이스의 화면 해상도로 프리뷰를 표시합니다.

### @PreviewParameter로 다중 프리뷰 만들기 {#preview-parameter}

`@PreviewParameter` 어노테이션은 `PreviewParameterProvider` 를 통해 컴포저블 함수에 미리 정의한 데이터를 주입할 수 있게 해 줍니다. [PreviewParameterProvider](https://developer.android.com/reference/kotlin/androidx/compose/ui/tooling/preview/PreviewParameterProvider)를 구현한 커스텀 클래스를 만들어 다양한 데이터셋을 공급하면, **동적인 프리뷰** 를 손쉽게 구성할 수 있습니다.

```kotlin
data class User(
    val name: String,
)

class UserPreviewParameterProvider : PreviewParameterProvider&lt;User&gt; {
    override val values: Sequence&lt;User&gt;
        get() = sequenceOf(
            User("user1"),
            User("user2"),
        )
}

@Preview(name = "UserPreview")
@Composable
private fun UserPreview(
    @PreviewParameter(provider = UserPreviewParameterProvider::class) user: User
) {
    Text(text = user.name, color = Color.White)
}
```
{title="ParameterizedPreview.kt"}

이 패턴은 제공된 값들을 기반으로 여러 프리뷰 변형을 자동으로 만들어 줍니다. Jetpack Compose UI tooling 라이브러리는 [LoremIpsum](https://cs.android.com/androidx/platform/frameworks/support/+/androidx-main:compose/ui/ui-tooling-preview/src/commonMain/kotlin/androidx/compose/ui/tooling/preview/datasource/LoremIpsum.kt) 같은 미리 정의된 `PreviewParameterProvider` 도 제공해, 프리뷰용 샘플 텍스트를 쉽게 채워 넣을 수 있게 해 줍니다.

```kotlin
@Preview
@Composable
private fun TestPreview(@PreviewParameter(provider = LoremIpsum::class) text: String) {
    Text(text = text, color = Color.White)
}
```
{title="LoremIpsum.kt"}

### Preview의 인터랙티브 모드 {#interactive-mode}

Android Studio는 인터랙티브 프리뷰를 지원해 앱 실행 없이도 컴포저블과 직접 상호작용할 수 있게 해 줍니다.

```kotlin
@Preview(showBackground = true)
@Composable
fun InteractivePreview() {
    var count by remember { mutableStateOf(0) }

    Column {
        Text("Count: $count")
        Button(onClick = { count++ }) {
            Text("Increment")
        }
    }
}
```
{title="InteractivePreview.kt"}

클릭 가능한 요소, 애니메이션, 상태 갱신을 Preview 창에서 그대로 시험해 볼 수 있습니다. Android Studio의 Preview 창에서 인터랙티브 모드를 켜면 컴포저블과 즉시 상호작용할 수 있습니다.

### MultiPreview 어노테이션 {#multipreview-annotations}

앞서 살펴봤듯 `@Preview` 어노테이션은 반복 적용이 가능합니다. Jetpack Compose는 여러 UI 조건을 효율적으로 테스트할 수 있는 내장 멀티 프리뷰 어노테이션도 제공합니다. `@PreviewLightDark`, `@PreviewFontScale`, `@PreviewDynamicColors`, `@PreviewScreenSizes` 같은 어노테이션이 대표적입니다.

예를 들어 라이트/다크 모드를 동시에 프리뷰하려면 두 어노테이션을 함께 적용할 수도 있고,

```kotlin
@Preview(name = "light mode")
@Preview(name = "dark mode", uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun MyPreview() {
    // ...
}
```
{title="MultiPreviewAnnotations.kt"}

또는 `@PreviewLightDark` 한 줄로 같은 효과를 낼 수도 있습니다.

```kotlin
@PreviewLightDark
@Composable
private fun MyPreview() {
    // ...
}
```
{title="MultiPreviewAnnotations.kt"}

`@PreviewScreenSizes` 와 `@PreviewFontScale` 같은 사전 정의된 멀티 프리뷰 어노테이션을 함께 조합하면, 다양한 화면 크기와 글자 크기에 걸친 변화를 한 화면에서 확인할 수 있어 수동으로 구성을 바꾸지 않고도 효율적인 테스트가 가능합니다.

### 요약 {#summary}

<tldr>

`@Preview` 는 Android Studio 안에서 실시간 렌더링과 커스터마이즈, 인터랙션 모드를 제공해 UI 개발의 흐름을 매끄럽게 만들어 줍니다. 테마, 디바이스 구성, 다크 모드, 파라미터화된 입력까지 폭넓게 지원하므로 프로젝트 전체를 빌드하지 않고도 컴포저블의 다양한 모습을 빠르게 확인할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) @Preview 어노테이션은 개발 흐름을 어떻게 개선해 주며, 자주 활용한 핵심 설정(다크 테마, 화면 크기, 멀티 프리뷰 어노테이션 등)은 무엇인가요?">

`@Preview` 가 가져오는 가장 큰 이점은 **빠른 시각적 피드백 루프** 입니다. 컴포저블 한 줄을 수정하고도 전체 빌드 없이 Preview 창에서 그 결과를 즉시 확인할 수 있어, 디자인 시스템 작업이나 카드/버튼 같은 작은 컴포넌트를 다듬을 때 작업 속도가 체감상 크게 빨라집니다. 인터랙티브 모드까지 켜면 클릭 핸들러나 애니메이션도 앱 실행 없이 그대로 시험해 볼 수 있어, 디자인 변경 → 검증 사이의 시간이 매우 짧아집니다.

자주 활용하는 설정 조합은 보통 세 갈래입니다. 첫째는 **테마/모드** 입니다. `@PreviewLightDark` 한 줄로 라이트·다크 모드를 동시에 보여 주거나, `uiMode = Configuration.UI_MODE_NIGHT_YES` 와 `showBackground = true` 를 묶어 다크 모드 컴포넌트의 시각 검증에 활용합니다. 둘째는 **화면 크기와 폰트 스케일** 로, `@PreviewScreenSizes` 와 `@PreviewFontScale` 을 함께 적용해 작은 화면이나 큰 글씨 모드에서의 레이아웃 깨짐을 미리 잡아냅니다. 마지막은 **데이터 변형** 으로, `@PreviewParameter` 와 커스텀 `PreviewParameterProvider` 를 활용해 빈 상태/로딩/에러/긴 텍스트 같은 엣지 케이스를 한 번에 늘어놓고 검토합니다.

이 패턴들은 디자인 시스템 컴포넌트 단위로 묶어 두는 것이 가장 효율적입니다. 예를 들어 `@PreviewLightDark @PreviewFontScale @PreviewScreenSizes` 세 어노테이션을 결합한 커스텀 멀티 프리뷰 어노테이션을 하나 만들어 두면, 새 컴포넌트를 만들 때마다 그 어노테이션 한 줄만 붙이면 라이트/다크 × 폰트 스케일 × 화면 크기의 모든 조합을 동시에 확인할 수 있습니다. 디자인 검수와 회귀 방지를 동시에 챙기는 가장 가성비 좋은 패턴입니다.

</def>
</deflist>
