# Android Manifest Notes

이 문서는 [skydoves/manifest-android-interview](https://github.com/skydoves/manifest-android-interview) 내용을 기반으로 안드로이드 핵심 CS 지식을 학습하고 정리한 프로젝트입니다.

## 학습 목차

### 1.1 Android Framework

Android 플랫폼의 기본 구조와 핵심 개념들을 다룹니다.

- [Q1. Android란?](Q1-Android.md) - Android 운영체제의 기본 개념과 아키텍처
- [Q2. Intent](Q2-Intent.md) - 컴포넌트 간 통신을 위한 Intent 시스템
- [Q3. PendingIntent](Q3-Pending-Intent.md) - 지연 실행을 위한 PendingIntent  
- [Q4. Serializable & Parcelable](Q4-Serializable-Parcelable.md) - 객체 직렬화 방법들
  - [Details: Parcel and Parcelable](Details-Parcel-and-Parcelable.md)
- [Q5. Context](Q5-Context.md) - Android의 Context 개념과 올바른 사용법
  - [Details: 올바른 Context 사용법](Details-올바른-Context-사용법.md)
  - [Details: ContextWrapper](Details-ContextWrapper.md)
  - [Details: This vs BaseContext](Details-This-vs-BaseContext.md)
- [Q6. Application Class](Q6-Application-Class.md) - Application 클래스의 역할과 활용
- [Q7. AndroidManifest](Q7-AndroidManifest.md) - 앱 구성 정보를 담는 매니페스트 파일
- [Q8. Activity Lifecycle](Q8-Activity-LifeCycle.md) - 액티비티 생명주기 관리
  - [Details: Lifecycle 인스턴스란](Details-Lifecycle-인스턴스란.md)
  - [Details: 여러 Activity 간 수명 주기 변화](Details-여러-Activity-간-수명-주기-변화.md)

### 1.2 ETC

이 외로 추가적인 내용을 다룹니다.

- [E1. RecyclerView 렌더링 과정](E1-RecyclerView-렌더링-과정.md) - 효율적인 리스트 구현을 위한 RecyclerView
