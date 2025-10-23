# Q26) 접근성

## 접근성을 어떻게 보장하나요?

접근성은 시각, 청각, 신체 장애가 있는 사람들을 포함하여 모든 사람이 애플리케이션을 사용할 수 있도록 보장합니다.
접근성 기능을 구현하면 사용자 경험이 향상되고 `WCAG` (Web Content Accessibility Guidelines)와 같은 글로벌 접근성 표준을 준수할 수 있습니다.

### ContentDescription 활용

콘텐츠 설명은 `UI` 요소에 텍스트 레이블을 제공하여 [TalkBack](https://support.google.com/accessibility/android/answer/6283677)과 같은 화면 판독기가 시각 장애가 있는 사용자에게 해당 요소를 알릴 수 있도록 합니다.
버튼, 이미지, 아이콘과 같은 대화형 또는 정보성 요소에는 `android:contentDescription` 속성을 사용합니다.
요소가 장식용이며 화면 판독기가 무시해야 하는 경우 `android:contentDescription`을 `null`로 설정하거나 `View.IMPORTANT_FOR_ACCESSIBILITY_NO`를 사용합니다.

```xml
    <ImageView
        android:contentDescription="Profile Picture"
        android:src="@drawable/profile_image" />
```

### 동적 글꼴 크기 지원

앱이 기기 설정에서 사용자가 설정한 글꼴 크기 기본 설정을 따르도록 합니다.
접근성 설정에 따라 자동으로 크기가 조정되도록 텍스트 크기에는 `sp` 단위를 사용합니다.

```xml
    <TextView
        android:textSize="16sp"
        android:text="Sample Text" />
```

### 포커스 관리 및 탐색

특히 사용자 지정 뷰, 다이얼로그 및 폼의 포커스 동작을 올바르게 관리합니다.
`android:nextFocusDown`, `android:nextFocusUp` 및 관련 속성을 사용하여 키보드 및 `D-pad` 사용자를 위한 논리적인 탐색 경로를 정의합니다.
또한 화면 판독기로 앱을 테스트하여 요소 간에 포커스가 자연스럽게 이동하는지 확인합니다.

### 색상 대비 및 시각적 접근성

저시력 또는 색맹 사용자의 가독성을 높이기 위해 텍스트와 배경색 사이에 충분한 대비를 제공합니다.
`Android Studio`의 `Accessibility Scanner`와 같은 도구는 앱의 색상 대비를 평가하고 최적화하는 데 도움이 될 수 있습니다.

### CustomView 및 접근성

사용자 지정 뷰를 만들 때 `AccessibilityDelegate`를 구현하여 화면 판독기가 사용자 지정 `UI` 구성 요소와 상호 작용하는 방식을 정의합니다.
`onInitializeAccessibilityNodeInfo()` 메서드를 재정의하여 사용자 지정 요소에 대한 의미 있는 설명과 상태를 제공합니다.

```kotlin
    class CustomView(context: Context) : View(context) {
        init {
            importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_YES
            setAccessibilityDelegate(object : AccessibilityDelegate() {
                override fun onInitializeAccessibilityNodeInfo(
                    host: View, info:
                    AccessibilityNodeInfo
                ) {
                    super.onInitializeAccessibilityNodeInfo(host, info)
                    info.text = "Custom component description"
                }
            })
        }
    }
```

### 접근성 테스트

`Android Studio`의 `Accessibility Scanner` 및 `Layout Inspector`와 같은 도구를 사용하여 접근성 문제를 식별하고 해결합니다.
이러한 도구는 앱이 보조 기술을 사용하는 사용자에게 접근 가능한지 확인하는 데 도움이 됩니다.

### 요약

`Android` 애플리케이션에서 접근성을 보장하는 것은 콘텐츠 설명을 제공하고, `sp` 단위를 사용하여 동적 글꼴 크기를 지원하고, 탐색을 위한 포커스를 관리하고, 적절한 색상 대비를 보장하고, 사용자 지정 뷰에 대한 접근성 지원을 추가하는 것을 포함합니다.
`Android` 도구를 활용하고 철저히 테스트함으로써 모든 사용자에게 포괄적이고 접근 가능한 애플리케이션을 구축할 수 있습니다.
접근성에 대한 자세한 내용은 아래 공식 문서를 확인하세요:

* [앱 접근성 개선](https://developer.android.com/guide/topics/ui/accessibility/apps)
* [앱 접근성 개선 원칙](https://developer.android.com/guide/topics/ui/accessibility/principles)
* [앱 접근성 테스트](https://developer.android.com/guide/topics/ui/accessibility/testing)

> Q) 동적 글꼴 크기를 지원하기 위한 모범 사례는 무엇이며, 텍스트 크기에 `sp` 단위를 사용하는 것이 `dp`보다 선호되는 이유는 무엇인가요?
>
> Q) 개발자는 보조 기술을 사용하는 사용자를 위해 올바른 포커스 관리 및 탐색을 어떻게 보장할 수 있으며, 접근성 문제를 테스트하는 데 어떤 도구가 도움이 될 수 있나요?