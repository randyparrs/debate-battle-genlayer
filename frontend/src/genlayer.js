import { createClient, simulator } from "@genlayer/js";

export const client = createClient({
  ...simulator,
});

export const CONTRACT_ADDRESS = "0xYourContractAddressHere";
