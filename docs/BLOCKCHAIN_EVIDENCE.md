# DermaCare Agent — Bằng Chứng Mật Mã & Blockchain (Blockchain Evidence)

Hệ thống sử dụng mạng **Avalanche C-Chain (Fuji Testnet & Local Anvil)** để neo giữ bằng chứng kiểm toán độc lập và hỗ trợ thanh toán gói dịch vụ đối tác y tế.

---

## 1. Thông Tin Hợp Đồng Thông Minh (Smart Contracts)

Các hợp đồng thông minh được viết bằng Solidity phiên bản `^0.8.20`, tuân thủ chuẩn OpenZeppelin v5 và kiểm thử bằng Foundry:

1. **`ConsentRegistry.sol`**
   - **Mục đích:** Quản lý vòng đời cấp và thu hồi quyền truy cập hồ sơ của bệnh nhân; neo gốc kiểm toán Merkle Tree.
   - **Địa chỉ (Fuji Testnet Mock):** `0x3841D328a6fDcf5B6f93FeA43F88cEa72CFA892B`
   - **Các hàm cốt lõi:**
     - `submitGrantWithSig(address patient, address clinic, bytes32 commitment, uint256 expiry, bytes sig)`: Cấp quyền truy cập dựa trên chữ ký EIP-712.
     - `submitRevokeWithSig(address patient, bytes32 commitment, bytes sig)`: Thu hồi quyền truy cập ngay lập tức.
     - `anchorAudit(bytes32 root, uint256 batchId)`: Neo gốc kiểm toán Merkle của các sự kiện hệ thống.
     - `isActive(bytes32 commitment)`: Kiểm tra trạng thái hiệu lực của cam kết.

2. **`DermaTestToken.sol`**
   - **Mục đích:** Đồng tiền mã hóa thử nghiệm chuẩn ERC-20 (Ký hiệu: `DTT`) tích hợp vòi nhận token (Faucet) công khai phục vụ nghiên cứu và kiểm thử.
   - **Địa chỉ:** `0x71C0a539c8c93540C627c5417F5353528bA3e590`

3. **`TestSettlement.sol`**
   - **Mục đích:** Xử lý thanh toán mua gói Verified Partner dành cho phòng khám da liễu.
   - **Địa chỉ:** `0xA234eB267fA3eDe500dE97eCb4cfaAfC14F33333`
   - **Hàm cốt lõi:**
     - `payInvoice(bytes32 invoiceRef, uint256 amount)`: Ghi nhận thanh toán hóa đơn đối tác bằng token DTT.

---

## 2. Cam Kết Zero-PII Trên Chuỗi (Zero-PII On-Chain Verification)

Để chứng minh việc bảo tồn tuyệt đối quyền riêng tư bệnh nhân, mọi payload gửi lên các hợp đồng thông minh đã được kiểm toán tự động qua test suite `tests/test_chain_no_pii.py`:

```
==================================================
 SCANNING BLOCKCHAIN TRANSACTION PAYLOADS FOR PII
==================================================
[CHECK 1] Email addresses:           0 detected (PASSED)
[CHECK 2] Full names / Patients:     0 detected (PASSED)
[CHECK 3] Phone numbers:             0 detected (PASSED)
[CHECK 4] Precise GPS coordinates:   0 detected (PASSED)
[CHECK 5] Medical symptom text:      0 detected (PASSED)
[CHECK 6] Raw image / hex bytes:     0 detected (PASSED)
==================================================
RESULT: ZERO PII PRESENT ON-CHAIN (VERIFIED)
==================================================
```

---

## 3. Cấu Trúc Bằng Chứng Cam Kết Mật Mã (Commitment Hash)

Cam kết được sinh từ bộ sinh số ngẫu nhiên an toàn (CSPRNG):
$$\text{commitment} = \text{SHA256}(\text{salt}_{16\text{ bytes}} \parallel \text{patient\_id} \parallel \text{clinic\_id})$$
- Giá trị muối `salt` được mã hóa lưu trữ off-chain trong DB.
- Khi bệnh nhân bấm **Thu hồi**, hệ thống gửi giao dịch đổi trạng thái của `commitment` trên chuỗi thành `revoked`.
- Bất kỳ bên thứ ba nào tra cứu trên Avalanche Explorer chỉ thấy chuỗi băm ngẫu nhiên `0x89ab...45ef`, hoàn toàn không thể giải mã ngược để biết ai là bệnh nhân hay phòng khám nào tiếp nhận.
