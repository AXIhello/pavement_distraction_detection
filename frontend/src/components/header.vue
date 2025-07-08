<template>
  <div class="navigation">
    <div class="text-wrapper">交通检测系统</div>
    <div class="items">
      <div class="group">
        <div class="div">路面灾害检测</div>
      </div>
      <div class="text-wrapper-2">城市交通时空</div>
      <div class="text-wrapper-2">日志</div>
      <button class="button">
        <div class="text-wrapper-3">用户中心</div>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: "Navigation",
};
</script>

<style>
.navigation {
  background-color: var(--navigation-bar);
  height: 164px;
  position: relative;
  width: 1440px;
}

.navigation .text-wrapper {
  color: #000000;
  font-family: "Inter-Medium", Helvetica;
  font-size: 45px;
  font-weight: 500;
  height: 68px;
  left: 80px;
  letter-spacing: 0;
  line-height: 67.5px;
  position: absolute;
  top: 47px;
  white-space: nowrap;
}

.navigation .items {
  align-items: center;
  display: flex;
  gap: var(--variable-collection-spacing-m);
  height: 78px;
  justify-content: flex-end;
  left: 743px;
  position: absolute;
  top: 48px;
  width: 636px;
}

.navigation .group {
  height: 37.32px;
  position: relative;
  width: 146px;
}

.navigation .div {
  color: #000000;
  font-family: "Inter-Medium", Helvetica;
  font-size: 24px;
  font-weight: 500;
  height: 37px;
  left: 0;
  letter-spacing: 0;
  line-height: 36px;
  position: absolute;
  top: 0;
  white-space: nowrap;
  width: 144px;
}

.navigation .text-wrapper-2 {
  color: #000000;
  font-family: "Inter-Medium", Helvetica;
  font-size: 24px;
  font-weight: 500;
  letter-spacing: 0;
  line-height: 36px;
  position: relative;
  white-space: nowrap;
  width: fit-content;
}

.navigation .button {
  all: unset;
  align-items: center;
  background-color: #000000;
  border-radius: 8px;
  box-shadow: var(--button-shadow);
  box-sizing: border-box;
  display: inline-flex;
  flex: 0 0 auto;
  gap: 8px;
  justify-content: center;
  padding: 14px 24px;
  position: relative;
}

.navigation .text-wrapper-3 {
  color: #ffffff;
  font-family: "Inter-Medium", Helvetica;
  font-size: 24px;
  font-weight: 500;
  letter-spacing: 0;
  line-height: 36px;
  margin-top: -1.00px;
  position: relative;
  white-space: nowrap;
  width: fit-content;
}
</style>