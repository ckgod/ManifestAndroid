# Details: PopupWindow

## PopupWindow란 무엇인가요? {#what-is-popup-window}

`PopupWindow`는 기존 레이아웃 위에 플로팅 팝업 View를 표시하는 UI 컴포넌트입니다. 화면 전체를 가리고 반드시 사용자 조작을 요구하는 Dialog와 달리, PopupWindow는 화면의 특정 위치에 유연하게 배치할 수 있으며 메뉴, 툴팁, 임시 UI 요소에 자주 활용됩니다.

### PopupWindow의 특징 {#popup-window-features}

- 커스터마이징 가능한 플로팅 View로 콘텐츠를 표시합니다.
- 화면을 어둡게 만들거나 차단하지 않아, 팝업 뒤의 다른 UI 컴포넌트와 상호작용이 가능합니다.
- 커스텀 레이아웃, 애니메이션, 닫기 동작을 지원합니다.
- 터치 기반 닫기와 포커스 제어로 자연스러운 사용자 경험을 제공합니다.

### PopupWindow 생성 및 표시 {#creating-popup-window}

```kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // 팝업에 사용할 커스텀 레이아웃 inflate
        val popupView = layoutInflater.inflate(R.layout.popup_layout, null)

        // PopupWindow 생성
        val popupWindow = PopupWindow(
            popupView,
            ViewGroup.LayoutParams.WRAP_CONTENT,
            ViewGroup.LayoutParams.WRAP_CONTENT,
            true // 포커스 활성화
        )

        // 팝업 외부 터치 시 닫기
        popupView.setOnTouchListener { _, _ ->
            popupWindow.dismiss()
            true
        }

        val button = findViewById<Button>(R.id.button)
        button.setOnClickListener {
            // 버튼 아래에 팝업 표시
            popupWindow.showAsDropDown(button)
        }
    }
}
```
{title="PopupWindowExample.kt"}

### Dialog와의 차이점 {#popup-vs-dialog}

`PopupWindow`는 언뜻 `Window`를 상속한 것처럼 보이지만, 실제로는 독립적인 클래스입니다. 내부적으로는 `WindowManager`를 사용하여 Window를 추가하고 제거하는 방식으로 동작합니다.

| 구분 | Dialog | PopupWindow |
|------|--------|-------------|
| 화면 dim 처리 | 있음 | 없음 |
| 배경 상호작용 | 불가 | 가능 |
| 위치 지정 | 중앙 고정 | 임의 위치 지정 가능 |
| 용도 | 사용자 확인/입력 | 메뉴, 툴팁, 임시 UI |

### 요약 {#summary}

`PopupWindow`는 Android에서 플로팅 UI 요소를 표시하는 데 유용한 도구입니다. 커스텀 레이아웃과 유연한 위치 지정 덕분에 컨텍스트 메뉴, 툴팁, 임시 팝업처럼 메인 앱 흐름을 방해하지 않으면서 사용자 상호작용을 풍부하게 만드는 UI 구현에 적합합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) PopupWindow와 Dialog 중 어떤 상황에서 무엇을 선택해야 하나요?">

**Dialog를 선택해야 하는 경우:**
- 사용자에게 "확인" 또는 "취소" 같은 명시적인 응답을 요구할 때
- 중요한 경고나 오류 메시지를 전달할 때
- 사용자가 응답하기 전까지 다른 작업을 차단해야 할 때

**PopupWindow를 선택해야 하는 경우:**
- 특정 View에 앵커링된 컨텍스트 메뉴나 옵션 목록을 표시할 때
- 툴팁처럼 사용자의 작업 흐름을 방해하지 않는 정보 제공 UI
- 뒤의 화면과 계속 상호작용이 필요한 경우

간단한 목록 선택의 경우 `ListPopupWindow`나 `DropDownMenu`를 사용하면 더 간결하게 구현할 수 있습니다.

</def>
</deflist>
