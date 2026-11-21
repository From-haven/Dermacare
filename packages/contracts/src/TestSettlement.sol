// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/**
 * @title TestSettlement
 * @notice Test settlement contract for Verified Partner packages.
 * ZERO PII on-chain: invoiceRef is a random bytes32.
 */
contract TestSettlement {
    address public immutable tokenAddress;
    address public treasury;

    mapping(bytes32 => bool) public paidInvoices;

    event InvoicePaid(bytes32 indexed invoiceRef, address indexed clinicWallet, uint256 amount);

    constructor(address _tokenAddress, address _treasury) {
        tokenAddress = _tokenAddress;
        treasury = _treasury;
    }

    function payInvoice(bytes32 invoiceRef, address clinicWallet, uint256 amount) external {
        require(!paidInvoices[invoiceRef], "Invoice already paid");
        require(amount > 0, "Invalid amount");

        paidInvoices[invoiceRef] = true;
        bool ok = IERC20(tokenAddress).transferFrom(clinicWallet, treasury, amount);
        require(ok, "Transfer failed");

        emit InvoicePaid(invoiceRef, clinicWallet, amount);
    }
}
