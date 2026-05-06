# Q40) Screenshot Testing

## Screenshot 테스팅은 무엇이고, 개발 중 UI 일관성을 어떻게 보장해 주나요? {#what-is-screenshot-testing}

Screenshot 테스팅은 실제 디바이스에서 앱을 실행하지 않고도 UI 외양을 검증할 수 있는 효과적인 방법입니다. 새 스크린샷을 이전 스크린샷과 비교해 시각적인 변화를 감지할 수 있어, 변경이 일어난 영역을 손쉽게 식별할 수 있습니다. 또한 코드 리뷰에도 큰 도움이 됩니다. 팀원들이 코드 변경과 함께 UI 변경을 한눈에 보고 평가할 수 있기 때문입니다.

Jetpack Compose에서 screenshot 테스팅을 수행하는 방법은 크게 세 가지입니다. **Google이 공식 제공하는 Gradle 플러그인**, 그리고 커뮤니티 주도의 **Paparazzi** 와 **Roborazzi** 입니다. 각 접근은 UI 스냅샷을 효율적으로 캡처하고 비교하기 위한 고유한 장점을 제공합니다.

### Compose Screenshot Testing 플러그인 {#compose-screenshot-testing-plugin}

[Compose Screenshot Testing Plugin](https://developer.android.com/studio/preview/compose-screenshot-testing)은 Google이 공식적으로 제공하는 도구로, Compose Preview와 직접 통합되어 UI 스냅샷을 손쉽게 생성·비교할 수 있게 해 줍니다. UI 일관성을 확인하고 의도치 않은 레이아웃 변화를 감지하는 데 유용합니다.

screenshot 테스트는 UI 스냅샷을 캡처해 미리 승인된 참조 이미지(reference image)와 비교합니다. 차이가 발견되면 테스트가 실패하면서 변경 사항을 강조한 HTML 리포트를 생성합니다.

**Compose Preview Screenshot Testing 도구** 로 할 수 있는 일은 다음과 같습니다.

- screenshot 테스트 대상으로 컴포저블 프리뷰를 선택할 수 있습니다.
- 비교용 참조 이미지를 생성할 수 있습니다.
- UI 변경을 자동으로 감지하고 HTML 리포트를 생성합니다.
- `@Preview` 의 `uiMode`, `fontScale` 같은 파라미터를 활용해 테스트 커버리지를 확장할 수 있습니다.
- `screenshotTest` 소스 셋을 활용해 테스트를 모듈 단위로 구성할 수 있습니다.

이 접근은 UI 일관성을 보장하고 시각적 회귀를 효율적으로 잡아내는 데 도움이 됩니다.

### Paparazzi {#paparazzi}

[Paparazzi](https://github.com/cashapp/paparazzi)는 Cash App에서 개발한 오픈 소스 라이브러리로, 에뮬레이터나 실제 디바이스 없이도 screenshot 테스팅을 수행할 수 있게 해 줍니다. 전체가 JVM 위에서 동작하기 때문에 UI 스냅샷을 빠르고 효율적으로 캡처할 수 있습니다. Compose UI를 JVM에서 직접 렌더링하고 픽셀 단위로 비교 가능한 스크린샷을 생성하는 방식입니다.

```kotlin
class LaunchViewTest {
    @get:Rule
    val paparazzi = Paparazzi(
        deviceConfig = PIXEL_5,
        theme = "android:Theme.Material.Light.NoActionBar"
        // ... 더 많은 옵션은 문서를 참고합니다.
    )

    @Test
    fun launchView() {
        val view = paparazzi.inflate&lt;LaunchView&gt;(R.layout.launch)
        // 또는 ...
        // val view = LaunchView(paparazzi.context)

        view.setModel(LaunchModel(title = "paparazzi"))
        paparazzi.snapshot(view)
    }

    @Test
    fun launchComposable() {
        paparazzi.snapshot {
            MyComposable()
        }
    }
}
```
{title="Paparazzi.kt"}

### Roborazzi {#roborazzi}

[Roborazzi](https://github.com/takahirom/roborazzi)는 Jetpack Compose를 포함한 Android의 screenshot 테스팅을 위해 설계된 또 다른 오픈 소스 라이브러리입니다. UI 상태를 캡처하고 스냅샷 비교로 UI 변화를 검증할 수 있는 단순하고 유연한 API를 제공합니다.

Roborazzi는 [Robolectric](https://github.com/robolectric/robolectric)과 통합되어 동작하므로, 테스트가 Hilt와 함께 실행되거나 더 현실적인 환경에서 UI 컴포넌트와 상호작용할 수 있습니다. Robolectric을 활용해 스크린샷을 캡처하기 때문에, 테스트 과정의 효율성과 신뢰성을 높이면서도 의존성 주입이나 시스템 수준 상호작용과의 호환성도 함께 챙길 수 있습니다.

또한 [Compose Multiplatform 지원](https://takahirom.github.io/roborazzi/compose-multiplatform.html), [Compose Preview 통합](https://takahirom.github.io/roborazzi/preview-support.html), [AI 기반 이미지 검증](https://takahirom.github.io/roborazzi/ai-powered-image-assertion.html) 같은 기능도 함께 제공해 활용 폭이 넓습니다.

### 요약 {#summary}

<tldr>

Screenshot 테스팅은 UI 변화를 안정적으로 추적하고 디자인 일관성을 보장해 주는 도구입니다. Google의 Compose Screenshot Testing Plugin, Paparazzi, Roborazzi 모두 각자의 장점을 가지고 있어 개발 흐름에 맞춰 도입하기 좋습니다. screenshot 테스팅을 함께 사용하면 시각적 회귀를 일찍 감지하고 코드 리뷰의 효율을 높이며, 앱 버전을 가로질러 다듬어진 UI 경험을 유지할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 팀의 워크플로에 screenshot 테스팅을 도입한 적이 있다면, 개발이나 코드 리뷰 과정이 어떻게 개선되었나요? 어떤 구체적인 이점을 관찰했나요?">

가장 두드러지는 효과는 **코드 리뷰가 시각적인 변화로 바뀐다** 는 점입니다. 디자인 시스템 컴포넌트나 화면 단위 변경이 들어올 때, 텍스트 diff 만으로는 이 변경이 실제 UI에 어떤 영향을 주는지 가늠하기 어렵습니다. Screenshot 테스트가 자동으로 새 스냅샷과 기준 스냅샷의 diff 이미지를 만들어 주면, 리뷰어는 PR 페이지에서 곧바로 "이 변경이 어떤 픽셀을 어떻게 바꿨는가" 를 본 뒤 의견을 남길 수 있습니다. 이 한 가지만으로도 디자인 변경 PR의 리뷰 품질이 크게 올라갑니다.

두 번째 이점은 **시각적 회귀 방지** 입니다. 디자인 시스템의 토큰 변화, 폰트 변경, 다크 모드 색상 조정처럼 영향 범위가 넓은 변경은 코드 리뷰만으로는 모든 화면을 검증할 수 없습니다. screenshot 테스트가 라이트/다크 모드, 화면 크기, 폰트 스케일 등의 조합으로 자동 캡처를 만들어 두면, 의도하지 않은 화면 한 곳에서 깨짐이 발생했을 때 그 시점에 곧바로 빨간불이 들어옵니다. 그 결과 디자인 시스템 변경의 비용이 크게 줄고, 의도된 변화와 의도하지 않은 변화를 분리해서 리뷰할 수 있게 됩니다.

다만 도입 시 주의할 점도 있습니다. 기준 스냅샷이 너무 자주 바뀌면 의미 있는 회귀를 일으키기보다는 "스냅샷 통과시키기" 가 일상이 되어 버립니다. 그래서 디자인 시스템 컴포넌트나 핵심 화면 정도로 대상 범위를 좁히고, PR 단계에서 스냅샷 갱신을 명시적으로 정당화하도록 흐름을 잡는 것이 좋습니다. 또한 폰트 렌더링이나 안티앨리어싱 차이로 인한 미세 차이가 false positive 를 만들 수 있으므로, 비교 알고리즘의 허용 오차나 마스킹 영역(예: 시간 표시) 같은 옵션을 함께 다듬어야 안정적으로 운영됩니다.

</def>
</deflist>
